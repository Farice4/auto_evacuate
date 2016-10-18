Name:       eayunstack-auto-evacuate
Version:    1.0
Release:    5%{?dist}
Summary:    EayunStack Auto Evacuate Tool

Group:      Application
License:    GPL
URL:        http://gitlab.eayun.com:9000/eayunstack/auto-evacuate/
Source0:    eayunstack-auto-evacuate-%{version}.tar.gz

BuildRequires:  /bin/bash
BuildRequires:  python
BuildRequires:  python2-devel
BuildRequires:  python-setuptools
BuildRequires:  systemd
Requires:   python
Requires:   python-novaclient
Requires:   consul

%description
EayunStack Auto Evacuate Tool

%prep
%setup -q

%build
CFLAGS="$RPM_OPT_FLAGS" %{__python2} setup.py build

%install
rm -rf %{buildroot}
%{__python2} setup.py install --skip-build --root %{buildroot}
mkdir -p %{buildroot}/etc/autoevacuate/
cp evacuate.conf %{buildroot}/etc/autoevacuate/
install -p -D -m 755 eayunstack-auto-evacuate.service %{buildroot}%{_unitdir}/eayunstack-auto-evacuate.service


%files
%doc
%attr(0644, root,root)/etc/autoevacuate/evacuate.conf
%{_unitdir}/eayunstack-auto-evacuate.service
/usr/bin/autoevacuate
/usr/lib/python2.7/site-packages/


%changelog
* Tue Oct 18 2016 Chen Yuanbin <cybing4@gmail.com> 1.0-5
  Fix endless loop if something wrong happend when doing ipmi check

* Fri Aug 26 2016 blkart <blkart.org@gmail.com> 1.0-4
  add systemd to rpm buildrequires

* Fri Aug 26 2016 Chen Yuanbin <cybing4@gmail.com> 1.0-3
  Add Make file

* Wed Aug 24 2016 blkart <blkart.org@gmail.com> 1.0-2
  add systemd service

* Tue Aug 16 2016 Chen Yuanbin <cybing4@gmail.com> 1.0-1
  autoevacuate 1.0-1 version
