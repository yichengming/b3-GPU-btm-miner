#!/bin/bash

cd $(dirname $0)

if [ ! -f address.txt ];then
echo -e "\n file address.txt not exists! \n"
exit
fi

SMI=nvidia-smi

ADDR=$(cat address.txt | head -1 )

DRV=$( $SMI -h |grep Interface | awk -Fv '{print $2}' | cut -d. -f1 )
CARDS=$( $SMI -L | wc -l )

WK=$( /sbin/ifconfig |grep "inet" | head -1 |awk '{print $2}'|awk -F. '{print $3"x"$4}' )

if [ $DRV -lt 387 ];then
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:cuda8
echo CUDA = 8
else
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:cuda9
echo CUDA = 9
fi

echo "Driver = $DRV , CARD COUNT=$CARDS , WK=${WK}"

cd btm-miner

while true;do
./miner  -user ${ADDR}.${WK} $@  
sleep 5
done

