# NOTE
# - some useful urls:
#   - https://wiki.archlinux.org/index.php/Parallels
#   - http://download.parallels.com/desktop/v6/docs/en/Parallels_Desktop_Users_Guide/22570.htm
#
# Conditional build:
%bcond_without	kernel		# without kernel modules
%bcond_without	dist_kernel	# without distribution kernel
%bcond_without	userspace	# without userspace package

# this bcond needed to build 2.6.16 kernel, just up for now
%if "%{pld_release}" == "ac"
%bcond_without	up
%endif

%define		rel    	0.1
Summary:	Parallels Guest Utilities
Name:		prl-tools
Version:	6
Release:	%{rel}
License:	GPL
Group:		Applications/System
# Get this from your Mac having Parallels installed: /Library/Parallels/Tools/
Source0:	%{name}-lin.iso
# Source0-md5:	f3c1e1f57127a06d17bbb3ccb086f657
URL:		http://download.parallels.com/desktop/v6/docs/en/Parallels_Desktop_Users_Guide/22272.htm
BuildRequires:	/usr/bin/isoinfo
BuildRequires:	rpm >= 4.4.9-56
BuildRequires:	rpmbuild(macros) >= 1.453
%if %{with userspace}
%endif
%if %{with kernel} && %{with dist_kernel}
BuildRequires:	kernel%{_alt_kernel}-module-build >= 3:2.6.16
%endif
ExclusiveArch:	%{ix86} %{x8664}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

# constify %rel macro, so it wouldn't expand in kernel subpkgs
%{expand:%%global rel %{release}}

%description
Parallels Guest Utilities.

%package -n kernel%{_alt_kernel}-misc-prl
Summary:	Parallels Linux kernel modules
Release:	%{rel}@%{_kernel_ver_str}
Group:		Base/Kernel
Requires(post,postun):	/sbin/depmod
%if %{with dist_kernel}
%requires_releq_kernel
Requires(postun):	%releq_kernel
%endif

%description -n kernel%{_alt_kernel}-misc-prl
Parallels Linux kernel modules.

%prep
%setup -qcT

# unpack each file from .iso
image_file=%{SOURCE0}
for file in $(isoinfo -Rf -i $image_file); do
	[ $file = /installer ] && continue
	[ $file = /kmods ] && continue
	[ $file = /tools ] && continue
	[ $file = /tools/scripts ] && continue
	dir=$(dirname .$file)
	install -d $dir

	isoinfo -R -i $image_file -x $file > .$file
done

%{__tar} -xzf kmods/prl_mod.tar* -C kmods

cat << 'EOF' > kmods/prl_eth/pvmnet/Makefile
obj-m := prl_eth.o
prl_eth-objs := pvmnet.o
EOF

cat << EOF > kmods/prl_tg/Toolgate/Guest/Linux/prl_tg/Makefile
obj-m += prl_tg.o
prl_tg-objs := prltg.o

EXTRA_CFLAGS += -I$(pwd)/kmods/prl_tg
EXTRA_CFLAGS += -DPRL_INTERRUPTIBLE_COMPLETION
EOF

cat << EOF > kmods/prl_fs/SharedFolders/Guest/Linux/prl_fs/Makefile
obj-m := prl_tg.o
prl_tg-objs := super.o inode.o file.o interface.o

EXTRA_CFLAGS += -I$(pwd)/kmods/prl_fs
EXTRA_CFLAGS += -DPRLFS_IGET
EOF

%build
%if %{with kernel}
%build_kernel_modules -C kmods/prl_eth/pvmnet -m prl_eth
%build_kernel_modules -C kmods/prl_tg/Toolgate/Guest/Linux/prl_tg -m prl_tg
%build_kernel_modules -C kmods/prl_fs/SharedFolders/Guest/Linux/prl_fs -m prl_tg
%build_kernel_modules -C kmods/prl_fs_freeze/Snapshot/Guest/Linux/prl_freeze -m prl_fs_freeze
%endif

%if %{with userspace}
%endif

%install
rm -rf $RPM_BUILD_ROOT

%if %{with kernel}
%install_kernel_modules -d misc -m kmods/prl_eth/pvmnet/prl_eth
%install_kernel_modules -d misc -m kmods/prl_tg/Toolgate/Guest/Linux/prl_tg/prl_tg
# same module name, try renaming
%install_kernel_modules -d misc -m kmods/prl_fs/SharedFolders/Guest/Linux/prl_fs/prl_tg -s prl_fs
%install_kernel_modules -d misc -m kmods/prl_fs_freeze/Snapshot/Guest/Linux/prl_freeze/prl_fs_freeze
%endif

%if %{with userspace}
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post	-n kernel%{_alt_kernel}-misc-prl
%depmod %{_kernel_ver}

%if %{with userspace}
%files
%defattr(644,root,root,755)
%endif

%if %{with kernel}
%files -n kernel%{_alt_kernel}-misc-prl
%defattr(644,root,root,755)
/lib/modules/%{_kernel_ver}/misc/prl_eth.ko*
/lib/modules/%{_kernel_ver}/misc/prl_fs_freeze.ko*
/lib/modules/%{_kernel_ver}/misc/prl_tg.ko*
/lib/modules/%{_kernel_ver}/misc/prl_tg-prl_fs.ko*
%endif
