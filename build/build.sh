#! /bin/bash


DEV_CONTAINER_ID=`docker ps |grep developer-sandbox|awk '{print $1}'`
echo "dev_env container's id:"$DEV_CONTAINER_ID
echo "dev_env container's id:"$DEV_CONTAINER_ID > build_info.log

CONTRAIL_DIR=/root/contrail
VROUTER_DIR=/root/contrail/vrouter
DEV_ENV_DIR=/root/contrail-dev-env

COMMIT_ID=`docker exec $DEV_CONTAINER_ID git --git-dir=$VROUTER_DIR/.git --work-tree=$VROUTER_DIR log -n 1 --format=short|head -n 1|awk '{print $2}'`

echo "Latest commit id:"$COMMIT_ID
echo "Latest commit id:"$COMMIT_ID >> build_info.log
echo "Show git status and diff...\n"

docker exec $DEV_CONTAINER_ID git --git-dir=$VROUTER_DIR/.git --work-tree=$VROUTER_DIR status
docker exec $DEV_CONTAINER_ID git --git-dir=$VROUTER_DIR/.git --work-tree=$VROUTER_DIR diff

echo "Clean up the vrouter folder"
docker exec $DEV_CONTAINER_ID git --git-dir=$VROUTER_DIR/.git --work-tree=$VROUTER_DIR reset --hard HEAD

docker exec $DEV_CONTAINER_ID git --git-dir=$VROUTER_DIR/.git --work-tree=$VROUTER_DIR clean -xdf 

docker exec $DEV_CONTAINER_ID rm -rf $CONTRAIL_DIR/build/production/vrouter/dpdk/contrail-vrouter-dpdk

#TODO add proxy automatically
#use -e option for passing proxy into containers
docker exec $DEV_CONTAINER_ID make -C $DEV_ENV_DIR sync

docker exec $DEV_CONTAINER_ID scons -C /root/contrail -j 2 --opt=production

docker cp $DEV_CONTAINER_ID:$CONTRAIL_DIR/build/production/vrouter/dpdk/contrail-vrouter-dpdk .
