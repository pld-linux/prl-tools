# NOTE
# - some useful urls:
#   - https://wiki.archlinux.org/index.php/Parallels
#   - http://download.parallels.com/desktop/v6/docs/en/Parallels_Desktop_Users_Guide/22570.htm
#
# Conditional build:
%bcond_without	kernel		# without kernel modules
%bcond_without	dist_kernel	# without distribution kernel
%bcond_without	userspace	# without userspace package
%bcond_without	xorg		# without xorg parts (xorg/xfree is supported up to 11.x)

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
%if "%{pld_release}" == "ac"
BuildRequires:	XFree86-devel
%else
BuildRequires:	xorg-xserver-server-devel
%endif
%endif
%if %{with kernel} && %{with dist_kernel}
BuildRequires:	kernel%{_alt_kernel}-module-build >= 3:2.6.16
%endif
ExclusiveArch:	%{ix86} %{x8664}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

# constify %rel macro, so it wouldn't expand in kernel subpkgs
%{expand:%%global rel %{release}}

# So that building package on AC system won't write package name dep that Th system can't understand (libstdc++4)
%define		_noautoreqdep	libstdc++.so.6

%description
Parallels Guest Utilities.

%package -n xorg-driver-input-prlmouse
Summary:	X.org mouse driver for Parallels guest OS
Group:		X11/Applications
#Requires:	xorg-xserver-server >= 1.0.99.901
#Requires:	xorg-xserver-server(xinput-abi) <= 16.0
#Requires:	xorg-xserver-server(xinput-abi) >= 4.0

%description -n xorg-driver-input-prlmouse
X.org mouse driver for Parallels guest OS.

%package -n xorg-driver-video-prlvideo
Summary:	X.org video driver for Parallels guest OS
Group:		X11/Applications
#Requires:	Mesa-dri-driver-swrast
#Requires:	xorg-xserver-libdri >= 1.7.4
#Requires:	xorg-xserver-server >= 1.0.99.901
#Requires:	xorg-xserver-server(videodrv-abi) <= 12.0
#Requires:	xorg-xserver-server(videodrv-abi) >= 2.0

%description -n xorg-driver-video-prlvideo
X.org video driver for Paralllesguest OS.

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

cat version

# unpack userspace
%ifarch %{ix86}
src=prltools.tar.gz
%endif
%ifarch %{x8664}
src=prltools.x64.tar.gz
%endif
%{__tar} -xzf tools/$src -C tools

# unpack kernel
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
obj-m := prl_fs.o
prl_fs-objs := super.o inode.o file.o interface.o

EXTRA_CFLAGS += -I$(pwd)/kmods/prl_fs
EXTRA_CFLAGS += -DPRLFS_IGET
EOF

%build
%if %{with kernel}
%build_kernel_modules -m prl_eth -C kmods/prl_eth/pvmnet
%build_kernel_modules -m prl_tg -C kmods/prl_tg/Toolgate/Guest/Linux/prl_tg
%build_kernel_modules -m prl_fs -C kmods/prl_fs/SharedFolders/Guest/Linux/prl_fs
%build_kernel_modules -m prl_fs_freeze -C kmods/prl_fs_freeze/Snapshot/Guest/Linux/prl_freeze
%endif

%if %{with userspace}
%endif

%install
rm -rf $RPM_BUILD_ROOT

%if %{with kernel}
%install_kernel_modules -d misc -m kmods/prl_eth/pvmnet/prl_eth
%install_kernel_modules -d misc -m kmods/prl_tg/Toolgate/Guest/Linux/prl_tg/prl_tg
%install_kernel_modules -d misc -m kmods/prl_fs/SharedFolders/Guest/Linux/prl_fs/prl_fs
%install_kernel_modules -d misc -m kmods/prl_fs_freeze/Snapshot/Guest/Linux/prl_freeze/prl_fs_freeze

install -d $RPM_BUILD_ROOT/etc/modprobe.d/%{_kernel_ver}
cp -p installer/blacklist-parallels.conf $RPM_BUILD_ROOT/etc/modprobe.d/%{_kernel_ver}
%endif

%if %{with userspace}
install -d $RPM_BUILD_ROOT{%{_bindir},%{_sbindir},%{_libdir}}
install -p tools/bin/* $RPM_BUILD_ROOT%{_bindir}
install -p tools/sbin/* $RPM_BUILD_ROOT%{_sbindir}

%if %{with xorg}
install -d $RPM_BUILD_ROOT%{_libdir}/xorg/modules/{drivers,input}

%if "%{pld_release}" == "ac"
xorg_version=$(awk '/define.*XOrgReleaseString.*\./{print $NF}' %{_prefix}/X11R6/%{_lib}/X11/config/X11.tmpl)
%else
xorg_version=$(pkg-config --modversion xorg-server)
install -p tools/xorg.$xorg_version/usr/lib/libglx.so.1.0.0 $RPM_BUILD_ROOT%{_libdir}
%endif

install -p tools/xorg.$xorg_version/x-server/modules/input/prlmouse_drv.so $RPM_BUILD_ROOT%{_libdir}/xorg/modules/input
install -p tools/xorg.$xorg_version/x-server/modules/drivers/prlvideo_drv.so $RPM_BUILD_ROOT%{_libdir}/xorg/modules/drivers
%endif
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post	-n kernel%{_alt_kernel}-misc-prl
%depmod %{_kernel_ver}

%if %{with userspace}
%files
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/prl_istatus
%attr(755,root,root) %{_bindir}/prl_showvmcfg
%attr(755,root,root) %{_bindir}/prl_wmouse_d
%attr(755,root,root) %{_bindir}/prlhosttime
%attr(755,root,root) %{_sbindir}/prl-opengl-switcher.sh
%attr(755,root,root) %{_sbindir}/prl-xorgconf-fixer
%attr(755,root,root) %{_sbindir}/prl_nettool
%attr(755,root,root) %{_sbindir}/prl_snapshot
%endif

%if %{with xorg}
%files -n xorg-driver-input-prlmouse
%defattr(644,root,root,755)
%attr(755,root,root) %{_libdir}/xorg/modules/input/prlmouse_drv.so

%files -n xorg-driver-video-prlvideo
%defattr(644,root,root,755)
%attr(755,root,root) %{_libdir}/xorg/modules/drivers/prlvideo_drv.so
%endif

%if %{with kernel}
%files -n kernel%{_alt_kernel}-misc-prl
%defattr(644,root,root,755)
/etc/modprobe.d/%{_kernel_ver}/blacklist-parallels.conf
/lib/modules/%{_kernel_ver}/misc/prl_eth.ko*
/lib/modules/%{_kernel_ver}/misc/prl_fs.ko*
/lib/modules/%{_kernel_ver}/misc/prl_fs_freeze.ko*
/lib/modules/%{_kernel_ver}/misc/prl_tg.ko*
%endif
