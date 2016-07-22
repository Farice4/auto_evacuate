Name:       eayunstack-auto-evacuate
Version:    1.0
Release:    1%{?dist}
Summary:    EayunStack Auto Evacuate Tool

Group:      Application
License:    GPL
URL:        http://gitlab.eayun.com:9000/eayunstack/auto-evacuate/
Source0:    eayunstack-auto-evacuate-%{version}.tar.gz

BuildRequires:  /bin/bash
BuildRequires:  python
BuildRequires:  python2-devel
BuildRequires:  python-setuptools
Requires:   python
Requires:   python-novaclient
Requires:   consul
Requires:   pyghmi

%description
EayunStack Auto Evacuate Tool

%prep
%setup -q

%build
CFLAGS="$RPM_OPT_FLAGS" %{__python2} setup.py build

%install
rm -rf %{buildroot}
%{__python2} setup.py install --skip-build --root %{buildroot}


%files
%doc
%attr
/usr/lib/python2.7/site-packages/


%changelog

