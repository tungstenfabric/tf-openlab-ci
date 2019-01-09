import time
import unittest
import select
import datetime

import paramiko


server_list = {
        "controller": {
                "ipaddr": "10.10.10.18",
                "user": "root",
                "password": "tester"
            },
        "node1": {
                "ipaddr": "10.10.10.14",
                "user": "root",
                "password": "tester",
                "vm_ip": "169.254.0.6"
            },
        "node2": {
                "ipaddr": "10.10.10.95",
                "user": "root",
                "password": "tester",
                "vm_ip": "169.254.0.13"
            }
        }

test_VMs = ["VM2","VM3"]


class TFVPPVTestCase(unittest.TestCase):
    """Test throughput in VM(virtual machine) <-> Physical NIC <-> Physical NIC <-> VM (VPPV) topology
    """

    def _get_VMs_list(self, controller_client):
        stdin, stdout, stderr = controller_client.exec_command("nova list", timeout=30)
        
        stdout_lines = stdout.readlines()
        stderr_lines = stderr.readlines()
        
        if len(stdout_lines) == 0 or len(stderr_lines) > 0:

            for line in stderr_lines: 
                print line

            raise BaseException("Execute 'nova list' error")
        
        vm_list = []
        
        for line in stdout_lines[3:-1]: 
            vm_fields = line.split("|")
            vm = {"name": vm_fields[2].strip(),
                  "status": vm_fields[3].strip()}
            vm_list.append(vm)

        return vm_list


    def _start_VM(self, controller_client, vm_name, skip_err=True):
        stdin, stdout, stderr = controller_client.exec_command("nova start " + vm_name)

        stdout_lines = stdout.readlines()
        stderr_lines = stderr.readlines()
        
        if len(stdout_lines) == 0 or len(stderr_lines) > 0:

            for line in stderr_lines: 
                print line

            if skip_err == False:
                raise BaseException("Execute 'nova start' error, vm=" + vm_name)

        print stdout_lines


    def _stop_VM(self, controller_client, vm_name, skip_err=True):
        stdin, stdout, stderr = controller_client.exec_command("nova stop " + vm_name)

        stdout_lines = stdout.readlines()
        stderr_lines = stderr.readlines()
        
        if len(stdout_lines) == 0 or len(stderr_lines) > 0:

            for line in stderr_lines: 
                print line

            if skip_err == False:
                raise BaseException("Execute 'nova stop ' error, vm=" + vm_name)

        print stdout_lines


    def _update_vrouter(self, node_client, vrouter_path):
        sftp = node_client.open_sftp()
        sftp.put(vrouter_path, './contrail-vrouter-dpdk-ci')
        sftp.chmod('./contrail-vrouter-dpdk-ci', 755)
        print "Start to update vrouter binary" 
        # TODO: Replace hardcoded core numbers ("10-17" in the command below) with input from a config file or environment
        # in order to support hardware platforms with different CPU core topologies
        stdin, stdout, stderr = node_client.exec_command("./change_vrouter_cores.sh contrail-vrouter-dpdk-ci 10-17", timeout=120)
        for line in stdout.readlines():
            print line

        print "Check the contrail-vrouter status, wait unit it becomes active"
        for i in range(5):
            stdin, stdout, stderr = node_client.exec_command("contrail-status", timeout=30)
            for line in stdout.readlines():
                print line
                if "agent: active" in line:
                    print "vRotuer launched"
                    return True
            time.sleep(30)

        raise BaseException("Deploy vRouter binary fail")


    def setUp(self):
        # Make sure /etc/kolla/admin-openrc.sh is executed in bashrc
        # Then it could be support nova command line
        print "Create ssh connection to controller"
        self.__srv_controller = paramiko.SSHClient()
        self.__srv_controller.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.__srv_controller.connect(server_list["controller"]["ipaddr"],
                                username=server_list["controller"]["user"],
                                password=server_list["controller"]["password"])

        print "Create ssh connection to node 1"
        self.__srv_node1 = paramiko.SSHClient()
        self.__srv_node1.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.__srv_node1.connect(server_list["node1"]["ipaddr"],
                                username=server_list["node1"]["user"],
                                password=server_list["node1"]["password"])

        print "Create ssh connection to node 2"
        self.__srv_node2 = paramiko.SSHClient()
        self.__srv_node2.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.__srv_node2.connect(server_list["node2"]["ipaddr"],
                                username=server_list["node2"]["user"],
                                password=server_list["node2"]["password"])

        # Update vRouter-dpdk binary to computer node
        self._update_vrouter(self.__srv_node1, "./contrail-vrouter-dpdk")
        self._update_vrouter(self.__srv_node2, "./contrail-vrouter-dpdk")

        time.sleep(60)
        
        print "Check the VMs status"
        VMs = self._get_VMs_list(self.__srv_controller)
        print VMs

        for vm in VMs:
            if vm["name"] in test_VMs:
                self._start_VM(self.__srv_controller, vm["name"])
                time.sleep(60) 

        print "Wait 120 secs for VMs boot up."        
        time.sleep(120)

        VMs = self._get_VMs_list(self.__srv_controller)
        for vm in VMs:
            if vm["name"] in test_VMs:
                if vm["status"] != "ACTIVE":
                    print "Launch VM failure, vm=" + vm["name"]
                    raise BaseException("Launch VM failure, vm=" + vm["name"])


    def testPMDThroughput(self):
        """Test DPDK PMD(polling mode driver) using TREX traffic generator https://trex-tgn.cisco.com/
        """
        print "PMD Throughput"
        try:
            chnn_trex = self.__srv_node1.invoke_shell()
            chnn_trex.send("ssh root@{0}\n".format(server_list["node1"]["vm_ip"]))
            time.sleep(10)

            chnn_trex.send("./run_test_trex.sh\n")
            time.sleep(20) 

            chnn_testpmd = self.__srv_node2.invoke_shell()
            chnn_testpmd.send("ssh root@{0}\n".format(server_list["node2"]["vm_ip"]))
            time.sleep(10)
            chnn_testpmd.send("./run_test_pmd.sh\n")
            time.sleep(20)

            chnn_tester = self.__srv_node1.invoke_shell()
            chnn_tester.send("ssh root@{0}\n".format(server_list["node1"]["vm_ip"]))
            chnn_tester.send("cd tra;python -u test.py\n")

            isDone = False
            result = ""
            
            start_time = datetime.datetime.now()
            timeout = 3600 
            while not isDone:
                end_time = datetime.datetime.now()
                if (end_time-start_time).seconds > timeout:
                    print "PMD throuputh test timeout"
                    raise BaseException("PMD throuputh test timeout")

                rl, wl, xl = select.select([chnn_trex, chnn_testpmd, chnn_tester], [], [], 0.0)
                if len(rl) > 0:
                    for chnn in rl:
                        out = chnn.recv(1024)
                        if chnn is chnn_tester:
                            result = result + out
                            print str(out)
                            if result.find("Done") != -1:
                                isDone = True
            
            print result 
            txt_perf_result = result.split("\r\n")[-3].split("=>")[1].strip()
            perf_num = int(txt_perf_result.split(" ")[0])*4
            perf_unit = txt_perf_result.split(" ")[1]

            with open("perf_pmd.xml","w") as xml_result:
                xml_result.write('<report name="PMDThroughputTest" categ="performance">')
                xml_result.write('<test name="PMDThroughput" executed="yes">')
                xml_result.write('<result>')
                xml_result.write('<success passed="yes" state="100"/>')
                xml_result.write('<performance unit="' + perf_unit + 
                                 '" mesure="' + str(perf_num) + 
                                 '" isRelevant="true"/>')
                xml_result.write('</result>')
                xml_result.write('</test>')
                xml_result.write('</report>')

        except Exception, ex:
            with open("perf_pmd.xml","w") as xml_result:
                xml_result.write('<report name="PMDThroughputTest" categ="performance">')
                xml_result.write('<test name="PMDThroughput" executed="yes">')
                xml_result.write('<result>')
                xml_result.write('<success passed="no" state="0"/>')
                xml_result.write('</result>')
                xml_result.write('</test>')
                xml_result.write('</report>')

        finally:
            chnn_tester.close()
            chnn_testpmd.close()
            chnn_trex.close()

    def testiPerfTCPThroughput(self):
        """Test virtio throughput (kernel vRouter) using iperf traffic generator https://iperf.fr/
        """
        print "iPerf TCP Throughput"
        try:
            chnn_srv = self.__srv_node1.invoke_shell()
            chnn_srv.send("ssh root@{0}\n".format(server_list["node1"]["vm_ip"]))
            time.sleep(10)

            chnn_srv.send("iperf3 -s\n")
            time.sleep(5) 

            chnn_clt = self.__srv_node2.invoke_shell()
            chnn_clt.send("ssh root@{0}\n".format(server_list["node2"]["vm_ip"]))
            time.sleep(10)
            chnn_clt.send("iperf3 -c 1.1.1.3 -P 16 -i 5 -t 30\n")

            time.sleep(5)

            isDone = False

            result = ""
            start_time = datetime.datetime.now()
            timeout = 120
            while not isDone:
                if chnn_clt.exit_status_ready():
                    break
                
                end_time = datetime.datetime.now()
                if (end_time-start_time).seconds > timeout:
                    print "iPerf TCP throuputh test timeout"
                    raise BaseException("iPerf TCP throuputh test timeout")

                rl, wl, xl = select.select([chnn_srv, chnn_clt], [], [], 0.0)
                if len(rl) > 0:
                    for chnn in rl:
                        out = chnn.recv(1024)
                        if chnn is chnn_clt:
                            result = result + out
                            print str(out)
                            if result.find("Done") != -1:
                                isDone = True

            print result
            result_throughput = result.split("\r\n")[-4].split("  ")[4].strip()
            perf_num, perf_unit = result_throughput.split(" ")
            
            with open("perf_iperf.xml","w") as xml_result:
                xml_result.write('<report name="iPerfThroughputTest" categ="performance">')
                xml_result.write('<test name="iPerfThroughput" executed="yes">')
                xml_result.write('<result>')
                xml_result.write('<success passed="yes" state="100"/>')
                xml_result.write('<performance unit="' + perf_unit + 
                                 '" mesure="' + str(perf_num) + 
                                 '" isRelevant="true"/>')
                xml_result.write('</result>')
                xml_result.write('</test>')
                xml_result.write('</report>')
        
        except Exception, ex:
            with open("perf_iperf.xml","w") as xml_result:
                xml_result.write('<report name="iPerfThroughputTest" categ="performance">')
                xml_result.write('<test name="iPerfThroughput" executed="yes">')
                xml_result.write('<result>')
                xml_result.write('<success passed="no" state="0"/>')
                xml_result.write('</result>')
                xml_result.write('</test>')
                xml_result.write('</report>')
        
        finally:
            chnn_clt.close()
            chnn_srv.close()



    def tearDown(self):
        VMs = self._get_VMs_list(self.__srv_controller)
        for vm in VMs:
            if vm["name"] in test_VMs:
                self._stop_VM(self.__srv_controller, vm["name"])
                time.sleep(60)
        time.sleep(120)

        VMs = self._get_VMs_list(self.__srv_controller)
        for vm in VMs:
            if vm["name"] in test_VMs:
                if vm["status"] != "SHUTOFF":
                    raise BaseException("Stop VM failure, vm=" + vm["name"])

        #self.__srv_controller.close()
        #self.__srv_node1.close()
        #self.__srv_node2.close()


if __name__ == "__main__":
#    unittest.main()
    tests = [
             'testiPerfTCPThroughput', 
             'testPMDThroughput',
            ]

    suite = unittest.TestSuite(map(TFVPPVTestCase, tests))
    results = unittest.TestResult()
    suite.run(results)




