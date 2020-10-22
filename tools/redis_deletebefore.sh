#!/bin/bash
CWD=$PWD
__file__=$(basename $0)
log_name=$(basename $__file__ .sh).log
logdir=$CWD/reports

function delete_before
{
    
    local backup_path=$logdir
    local backup_datas=$(ls -al $backup_path \
                         | grep ^d \
                         | awk '{print $NF}' \
                         | grep -Eo '[0-9]+' \
                         | sort -Vr)
    local data_lens=$(ls -al $backup_path \
                      | grep ^d \
                      | awk '{print $NF}' \
                      | grep -Eo '[0-9]+' \
                      | sort -Vr | wc -l)
    cd $backup_path
    if [ $data_lens -gt 24 ]; then
        local data_rm=($(ls . \
                        | grep -Eo '[0-9]+' \
                        | sort -Vr \
                        | sed -n 24,${#backup_datas[@]}p))
        for f in "${data_rm[@]}"
        do 
            echo -en "delete file ---> $backup_path/$f"
            rm -rf $f > /dev/null 2&>1
        done
    fi
    cd $CWD
    echo -e '\ndone!\n'
}

delete_before | tee $logdir/${log_name}
