docker run -it --device /dev/tenstorrent/0 \
	-v /dev/hugepages:/dev/hugepages \
	-v /dev/hugepages-1G:/dev/hugepages-1G \
	-v /etc/udev/rules.d:/etc/udev/rules.d \
	-v /lib/modules:/lib/modules \
	-v /localdev/dcvijetic:/localdev/dcvijetic \
	debuda-test bash