mkdir -p launch
logfilename="${1##*/}_$(date +%F_%H:%M:%S,%N)"

nohup mpirun -n $1 run_10_1type_ga.sh Test_Random_MPFA_r2_d1_tag64_5by5.xml>>launch/${logfilename}_stdout.log 2>> launch/${logfilename}_stderr.log &


#Command example: ./currentscript.sh numberHost*slots moses_cluster

