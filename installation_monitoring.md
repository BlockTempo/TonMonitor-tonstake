
- [ssh tunnel (intra net)](#ssh-tunnel-intra-net)
- [docker](#docker)
- [install fludntd](#install-fludntd)
  - [cfg](#cfg)
    - [fluentbit](#fluentbit)
- [promethus](#promethus)
    - [Create persistent volume for your data](#create-persistent-volume-for-your-data)
    - [Start Prometheus container](#start-prometheus-container)
      - [prerequisite](#prerequisite)
    - [install client](#install-client)
- [grafana](#grafana)
# ssh tunnel (intra net)

     gcloud compute ssh allenchan@ton-monitor  -- -L 8000:localhost:8080 -L 9090:localhost:9090 -L 3000:localhost:3000 -J allenchan@ton-office


# docker

    for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done

    # Add Docker's official GPG key:
    sudo apt-get update
    sudo apt-get install ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    # Add the repository to Apt sources:
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
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

## cfg

### fluentbit

Host

    sudo /opt/fluent-bit/bin/fluent-bit -i tail -p path=/home/allenchan/*.log -p db=logs.db -o forward://10.0.0.4:2021

create dir: `sudo mkdir /opt/ton-monitor/fluentbit -p`  
`sudo vi //etc/fluent-bit/fluent-bit.conf` 

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

Monitored host(agent config): (skipped, tonstake v2 install this by ansible)

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

# promethus
    

### Create persistent volume for your data

    docker volume create prometheus-data  

### Start Prometheus container
#### prerequisite
[enable api ](https://console.cloud.google.com/flows/enableapi?apiid=iam.googleapis.com&redirect=https://console.cloud.google.com&_ga=2.88757979.1139288775.1702380986-922422191.1699107769)  
create service account and grant permission
    - compute viewer
create service account sa file
    
    chmod 777 keys/sa.json

    #grant sa and get sa key file 
    gcloud iam service-accounts keys create /home/allenchan/keys/sa.json \
    --iam-account=prom-sd@tonstake-407311.iam.gserviceaccount.com
    #put to host and setup env vars to file path
    export GOOGLE_APPLICATION_CREDENTIALS="/home/allenchan/keys/sa.json"

    docker run \
        -p 9090:9090 \
        -v /home/allenchan/prometheus.yml:/etc/prometheus/prometheus.yml \
        -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/sa.json \
        -v /home/allenchan/keys/sa.json:/tmp/keys/sa.json \
        -v prometheus-data:/prometheus \
        -d \
        --restart=always \
        --name prometheus \
        prom/prometheus


config ./prometheus.yml

    global:
    scrape_interval: 5s

    scrape_configs:
    - job_name: node
        gce_sd_configs:
        - project: blocktempo
            zone: us-central1-a
            port: 9100
            filter: "labels.project=tonstake"
        relabel_configs:
        - source_labels: [__meta_gce_public_ip]
            target_label: public_ip
        - source_labels: [__meta_gce_private_ip]
            target_label: private_ip
        - source_labels: [__meta_gce_instance_name]
            target_label: instance_name
        - source_labels: [__meta_gce_instance_name]
            target_label: 'instance'
            regex: 'ton-stake-deployment-poc-(.+)'
            replacement: '$1'
    - job_name: python_wrap
        metrics_path: /
        gce_sd_configs:
        - project: blocktempo
            zone: us-central1-a
            port: 8888
            filter: "labels.project=tonstake"
        relabel_configs:
        - source_labels: [__meta_gce_public_ip]
            target_label: public_ip
        - source_labels: [__meta_gce_private_ip]
            target_label: private_ip
        - source_labels: [__meta_gce_instance_name]
            target_label: instance_name
        - source_labels: [__meta_gce_instance_name]
            target_label: 'instance'
            regex: 'ton-stake-deployment-poc-(.+)'
            replacement: '$1'

### install client

with ansible. 
add ip to prometheus.yaml 

# grafana

    # create a directory for your data
    mkdir grafana

    # start grafana with your user id and using the data directory
    docker run -d -p 3000:3000 --name=grafana \
    --user "$(id -u)" \
    --volume "$PWD/grafana:/var/lib/grafana" \
    --restart=always \
    grafana/grafana-enterprise

setup prom ip:port

     docker inspect prometheus | grep IP
