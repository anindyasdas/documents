export SSHPASS=dhlqndls!

DIR="$( cd "$( dirname "$0" )" && pwd -P )"
echo $DIR

cd ${DIR}/../apps/ker/dataset
sshpass -e sftp -oBatchMode=no -b - guest_ftp@10.178.138.108 << !
   get -r /Guest_Share_2021/APT_Share/knowledge-management-system/apps/ker/dataset
   bye
!

cd ${DIR}/../apps/ker/knowledge_extraction/server
sshpass -e sftp -oBatchMode=no -b - guest_ftp@10.178.138.108 << !
   get -r /Guest_Share_2021/APT_Share/knowledge-management-system/apps/ker/knowledge_extraction/server/image_db
   bye
!
