# SPDX-License-Identifier: GPL-2.0
SUDO ?= sudo
all: work
# ansible-playbook alias
%:
	@ansible-playbook $*.yaml -e latest=true -e build=true

.PHONY: dist-clean list ls
dist-clean: clean
	@$(RM) *.bak *.retry .*.sw? **/.*.sw?
	$(SUDO) $(RM) -rf .ansible
list ls:
	@docker images
	@$(SUDO) virsh net-list
	@$(SUDO) virsh list

# CI targets
.PHONY: ansible
ci-%: ci-ping-%
	ansible-playbook -vvv $*.yaml \
		-i inventory.yaml -c local -e ci=true -e gitsite=https://github.com/
ci-ping-%:
	ansible -vvv -m ping -i inventory.yaml -c local $*
ansible:
	git clone https://github.com/ansible/ansible .ansible
	cd .ansible \
		&& $(SUDO) pip install -r requirements.txt \
		&& $(SUDO) python setup.py install 2>&1 > /dev/null
