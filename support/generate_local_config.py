#!/usr/bin/env python3
# -*- coding: utf_8 -*-

import pwd
import random
import requests
import sys
sys.path.append('/usr/src/mytonctrl')
from mypylib.mypylib import *
from mypyconsole.mypyconsole import *

local = MyPyClass(__file__)
console = MyPyConsole()
defaultLocalConfigPath = "/usr/bin/ton/local.config.json"


def Init():
	local.db.config.isStartOnlyOneProcess = False
	local.db.config.logLevel = "warn"
	local.db.config.isIgnorLogWarning = True # disable warning
	local.run()
	local.db.config.isIgnorLogWarning = False # enable warning


	# create variables
	user = os.environ.get("USER", "root")
	local.buffer.user = user
	local.buffer.vuser = "validator"
	local.buffer.cport = random.randint(2000, 65000)
	local.buffer.lport = random.randint(2000, 65000)
	Refresh()
#end define

def Refresh():
	user = local.buffer.user
	local.buffer.mconfig_path = "/home/{user}/.local/share/mytoncore/mytoncore.db".format(user=user)
	if user == 'root':
		local.buffer.mconfig_path = "/usr/local/bin/mytoncore/mytoncore.db"
	#end if

	# create variables
	bin_dir = "/usr/bin/"
	src_dir = "/usr/src/"
	ton_work_dir = "/var/ton-work/"
	ton_bin_dir = bin_dir + "ton/"
	ton_src_dir = src_dir + "ton/"
	local.buffer.bin_dir = bin_dir
	local.buffer.src_dir = src_dir
	local.buffer.ton_work_dir = ton_work_dir
	local.buffer.ton_bin_dir = ton_bin_dir
	local.buffer.ton_src_dir = ton_src_dir
	ton_db_dir = ton_work_dir + "db/"
	keys_dir = ton_work_dir + "keys/"
	local.buffer.ton_db_dir = ton_db_dir
	local.buffer.keys_dir = keys_dir
	local.buffer.ton_log_path = ton_work_dir + "log"
	local.buffer.validator_app_path = ton_bin_dir + "validator-engine/validator-engine"
	local.buffer.global_config_path = ton_bin_dir + "global.config.json"
	local.buffer.vconfig_path = ton_db_dir + "config.json"
#end define

def get_own_ip():
	requests.packages.urllib3.util.connection.HAS_IPV6 = False
	ip = requests.get("https://ifconfig.me/ip").text
	return ip
#end define

def GetLiteServerConfig():
	keys_dir = local.buffer.keys_dir
	liteserver_key = keys_dir + "liteserver"
	liteserver_pubkey = liteserver_key + ".pub"
	result = Dict()
	file = open(liteserver_pubkey, 'rb')
	data = file.read()
	file.close()
	key = base64.b64encode(data[4:])
	ip = get_own_ip()
	mconfig = GetConfig(path=local.buffer.mconfig_path)
	result.ip = ip2int(ip)
	result.port = mconfig.liteClient.liteServer.port
	result.id = Dict()
	result.id["@type"]= "pub.ed25519"
	result.id.key= key.decode()
	return result
#end define

def GetInitBlock():
	from mytoncore import MyTonCore
	ton = MyTonCore()
	initBlock = ton.GetInitBlock()
	return initBlock
#end define

def CreateLocalConfig(initBlock, localConfigPath=defaultLocalConfigPath):
	# dirty hack, but GetInitBlock() function uses the same technique
	from mytoncore import hex2base64

	# read global config file
	file = open("/usr/bin/ton/global.config.json", 'rt')
	text = file.read()
	data = json.loads(text)
	file.close()

	# edit config
	liteServerConfig = GetLiteServerConfig()
	data["liteservers"] = [liteServerConfig]
	data["validator"]["init_block"]["seqno"] = initBlock["seqno"]
	data["validator"]["init_block"]["root_hash"] = hex2base64(initBlock["rootHash"])
	data["validator"]["init_block"]["file_hash"] = hex2base64(initBlock["fileHash"])
	text = json.dumps(data, indent=4)

	# write local config file
	file = open(localConfigPath, 'wt')
	file.write(text)
	file.close()

	# chown
	user = local.buffer.user
	args = ["chown", "-R", user + ':' + user, localConfigPath]

	print("Local config file created:", localConfigPath)
#end define

def GetConfig(**kwargs):
	path = kwargs.get("path")
	file = open(path, 'rt')
	text = file.read()
	file.close()
	config = Dict(json.loads(text))
	return config
#end define

###
### Start of the program
###

if __name__ == "__main__":
	Init()
	path = sys.argv.index("-o")
	configPath = sys.argv[path+1]
	initBlock = GetInitBlock()
	CreateLocalConfig(initBlock, configPath)
	local.exit()
#end if
