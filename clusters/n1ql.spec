[clusters]
n1ql =
    172.23.100.45:8091
    172.23.100.55:8091
    172.23.100.56:8091

[data]
n1ql =
    172.23.100.45
    172.23.100.55
    172.23.100.56

[n1ql]
n1ql =
    172.23.100.55

[index]
n1ql =
    172.23.100.56

[clients]
hosts =
    172.23.100.44
credentials = root:couchbase

[storage]
data = /data
index = /data1
secondary = /data1

[credentials]
rest = Administrator:password
ssh = root:couchbase

[parameters]
Platform = Physical
OS = CentOS 6.5
CPU = Intel Xeon E5-2680 (48 vCPU)
Memory = 256 GB
Disk = 2 x SSD

