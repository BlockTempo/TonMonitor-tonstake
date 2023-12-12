
- [ssh tunnel (intra net)](#ssh-tunnel-intra-net)
- [docker](#docker)
- [install fludntd](#install-fludntd)
  - [cfg](#cfg)
    - [fluentbit](#fluentbit)
- [isntall zabbix](#isntall-zabbix)
  - [default acc/pwd](#default-accpwd)
  - [setup zabbix monitor repo](#setup-zabbix-monitor-repo)
    - [import template](#import-template)
    - [import template - outdated](#import-template---outdated)
    - [install agent (on qa-1)](#install-agent-on-qa-1)
  - [promethus](#promethus)
    - [Create persistent volume for your data](#create-persistent-volume-for-your-data)
    - [Start Prometheus container](#start-prometheus-container)
    - [install client](#install-client)
    - [install blackbox exp on Prom host](#install-blackbox-exp-on-prom-host)
  - [grafana](#grafana)
# ssh tunnel (intra net)

     gcloud compute ssh allenchan@ton-monitor  -- -L 8000:localhost:8080 -L 9090:localhost:9090 -L 3000:localhost:3000 -J allenchan@ton-office


# docker

    for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done

    # Add Docker's official GPG key:
    sudo apt-get update
    sudo apt-get install ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg                                                                                                  
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg                                                                                                              
    # Add the repository to Apt sources:                                                                                                                     
    echo \                                                                                                                                                   
    "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \                             
    "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable"  \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null                                                                                                 
    sudo apt-get update                                                                                                                                      
                                                                                                                                                            
    sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin                                                    
                                                                                                                                                            
    sudo docker run hello-world
                                                                                                                                                            
    sudo groupadd docker                                                                                                                                     
    sudo usermod -aG docker $USER                                                                                                                            
    newgrp docker                                                                                                                                            
    docker run hello-world                                                                                                                                   
                                                                                                                                                            
    sudo systemctl enable docker.service                                                                                                                     
    sudo systemctl enable containerd.service                                                                                                                 
    #TODO setup log driver  https://docs.docker.com/engine/install/linux-postinstall/#configure-default-logging-driver                                       

# install fludntd

binary (fluent bit)

    curl https://raw.githubusercontent.com/fluent/fluent-bit/master/install.sh | sh
    sudo systemctl start fluent-bit.service
    sudo vi //etc/fluent-bit/fluent-bit.conf

    curl <https://packages.fluentbit.io/fluentbit.key>
    gpg --dearmor > /usr/share/keyrings/fluentbit-keyring.gpg

docker (tbd)

    docker stop $(docker ps -a -q)
    docker rm $(docker ps -a -q)

    mkdir log-data
    chmod 777 log-data/

    docker run -d -p 24224:24224 -p 24224:24224/udp -v ./log-data:/fluentd/log  -v ~/fluent.conf:/fluentd/etc/fluent.conf --name fluentd fluent/fluentd:edge
    tail -f fluentd/log/docker.log
    docker run --rm --log-driver=fluentd --log-opt fluentd-address=localhost:24224  tag=docker.{{.Name}}

## cfg

### fluentbit

Host

    sudo /opt/fluent-bit/bin/fluent-bit -i tail -p path=/home/allenchan/*.log -p db=logs.db -o forward://10.0.0.4:2021
    sudo /opt/fluent-bit/bin/fluent-bit -i tail -p path=/home/allenchan/*.log -o forward://10.0.0.4:2021

create dir: `sudo mkdir /opt/ton-monitor/fluentbit -p`

    [SERVICE]
    Flush 1
    Log_File /var/log/fluentbit.log
    Log_Level error
    Daemon off
    Parsers_File parsers.conf
    HTTP_Server On
    HTTP_Listen 0.0.0.0
    HTTP_Port 2020

    [INPUT]
    Name forward
    Listen 0.0.0.0
    Port 2021
    Buffer_Chunk_Size 32KB
    Buffer_Max_Size 6M

    [OUTPUT]
    Name file
    Match *
    Path /opt/ton-monitor/fluentbit
    ; Path /var/log/fluentbit

Monitored host

    # todo buffer host name info

    [SERVICE]
        Flush 1
        Daemon off
    [INPUT]
        Name tail
        Tag qa1.mytonctrl-api
        Path /home/allenchan/*.log
        DB logs.db
    [INPUT]
        Name tail
        Tag qa1.mytonctrl
        Path  /home/allenchan/.local/share/mytonctrl/mytonctrl.log
        DB logs.db
    [INPUT]
        Name tail
        Tag qa1.mytoncore
        Path  /home/allenchan/.local/share/mytoncore/mytoncore.log
        DB logs.db
    [INPUT]
        Name tail
        Tag qa1.validator
        Path /var/ton-work/*.log
        DB logs.db
    [OUTPUT]
        Name forward
        Match *
        Host 10.0.0.4
        Port 2021
---
<!-- <match docker.test>
@type elasticsearch
host localhost
port 9200
logstash_format true
</match>
<source>
@type  forward
@id    input1
@label @mainstream
port  24224
</source>

<filter **>
@type stdout
</filter>

<label @mainstream>
<match docker.**>
@type file
@id   output_docker1
path         /fluentd/log/docker.*.log
symlink_path /fluentd/log/docker.log
append       true
time_slice_format %Y%m%d
time_slice_wait   1m
time_format       %Y%m%dT%H%M%S%z
</match>
<match **>
@type file
@id   output1
path         /fluentd/log/data.*.log
symlink_path /fluentd/log/data.log
append       true
time_slice_format %Y%m%d
time_slice_wait   10m
time_format       %Y%m%dT%H%M%S%z
</match>
</label> -->

# isntall zabbix

    wget <https://repo.zabbix.com/zabbix/6.0/ubuntu/pool/main/z/zabbix-release/zabbix-release_6.0-4+ubuntu22.04_all.deb>
    sudo dpkg -i zabbix-release_6.0-4+ubuntu22.04_all.deb
    sudo apt update

    sudo apt install zabbix-server-mysql zabbix-frontend-php zabbix-apache-conf zabbix-sql-scripts zabbix-agent    mysql-server

    sudo mysql --defaults-file=/etc/mysql/debian.cnf
    mysql>
    create database zabbix character set utf8mb4 collate utf8mb4_bin;
    create user zabbix@localhost identified by 'password';
    grant all privileges on zabbix.* to zabbix@localhost;
    set global log_bin_trust_function_creators = 1;
    quit;

    sudo zcat /usr/share/zabbix-sql-scripts/mysql/server.sql.gz
    mysql --default-character-set=utf8mb4 -u zabbix -p zabbix
        password
    sudo mysql --defaults-file=/etc/mysql/debian.cnf
    mysql>
        set global log_bin_trust_function_creators = 0;

    # put in pws "DBPassword=password"  
    sudo vi /etc/zabbix/zabbix_server.conf 

    # sudo systemctl disable apache2.service
    # sudo systemctl stop apache2.service
    #  sudo systemctl daemon-reload   
    # sudo systemctl restart nginx.service

    # sudo systemctl restart zabbix-server zabbix-agent apache2
    # sudo systemctl enable zabbix-server zabbix-agent apache2
    sudo systemctl restart zabbix-server zabbix-agent nginx php8.1-fpm
    sudo systemctl enable zabbix-server zabbix-agent nginx php8.1-fpm

## default acc/pwd

Admin
zabbix

## setup zabbix monitor repo

    sudo apt install python3-pip
    pip install -r requirements.txt

    sudo vi /etc/zabbix/zabbix_server.conf
    # replace ExternalScripts /usr/lib/zabbix/externalscripts to /home/allenchan/ton-monitoring/scripts

### import template

### import template - outdated

config > template >create template> import

### install agent (on qa-1)
    <!-- export  CONFFILE=/home/allenchan/config_agent.json   -->
    wget https://repo.zabbix.com/zabbix/6.0/ubuntu/pool/main/z/zabbix-release/zabbix-release_6.0-4+ubuntu22.04_all.deb
    sudo dpkg -i zabbix-release_6.0-4+ubuntu22.04_all.deb
    sudo apt update

    sudo apt install zabbix-agent
    sudo systemctl restart zabbix-agent
    sudo systemctl enable zabbix-agent

    sudo vi /lib/systemd/system/zabbix-agent.service
    [Service]
    User=root
    Group=root
    sudo vi /etc/zabbix/zabbix_agentd.conf
    Server=127.0.0.1,10.0.0.0/16

config >　host> create host > interface > agent > ip
template liteclient

## promethus

### Create persistent volume for your data

    docker volume create prometheus-data  

### Start Prometheus container

    docker run \
        -p 9090:9090 \
        -v /home/allenchan/prometheus.yml:/etc/prometheus/prometheus.yml \
        -v prometheus-data:/prometheus \
        -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/sa.json \
        -v $GOOGLE_APPLICATION_CREDENTIALS:/tmp/keys/sa.json:ro \
        --name prometheus \
        --restart=always \
        -d \
        prom/prometheus

    #grant sa and get sa key file 
    put to host and setup env vars to file path

config
[./prometheus.yml](./prometheus.yml)

- job_name: 'blackbox_exporter'
    static_configs:
    - targets: ['127.0.0.1:9115']

### install client

with ansible. 
add ip to prometheus.yaml 

### install blackbox exp on Prom host

    touch blackbox.yml

    docker run -d --restart=always \
    -p 9115/tcp \
    --name blackbox_exporter \
    -v $(pwd):/config \
    quay.io/prometheus/blackbox-exporter:latest --config.file=/config/blackbox.yml

yml



## grafana

    # create a directory for your data
    mkdir grafana

    # start grafana with your user id and using the data directory
    docker run -d -p 3000:3000 --name=grafana \
    --user "$(id -u)" \
    --volume "$PWD/grafana:/var/lib/grafana" \
    grafana/grafana-enterprise

setup prom ip:port

     docker inspect prometheus | grep IP
