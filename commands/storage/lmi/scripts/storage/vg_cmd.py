# Storage Management Providers
#
# Copyright (C) 2013-2014 Red Hat, Inc. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of the FreeBSD Project.
#
# Authors: Jan Safranek <jsafrane@redhat.com>
#

"""
Volume Group management.

Usage:
    %(cmd)s list
    %(cmd)s create [ --extent-size=<size> ] <name> <device> ...
    %(cmd)s delete <vg> ...
    %(cmd)s show [ <vg> ...]

Commands:
    list        List all volume groups on the system.

    create      Create Volume Group with given name from list of devices.

    delete      Delete given Volume Groups.

    show        Show detailed information about given Volume Groups. If no
                Volume Groups are provided, all of them are displayed.

Options:

    device      Identifier of the device. Either one of:

                * DeviceID of appropriate CIM_StorageExtent object. This is
                  internal OpenLMI ID of the device and it should be stable
                  across system reboots.

                * Device name directly in /dev directory, such as '/dev/sda'.
                  This device name is available as Name property of
                  CIM_StorageExtent object.

                * Name of MD RAID or logical volume. This method cannot be used
                  when the name is not unique, for example when there are two
                  logical volumes with the same name, allocated from different
                  volume groups. This name is available as ElementName
                  property of CIM_StorageExtent object.

    vg          Name of the volume group, with or without `/dev/` prefix.

    size        Requested extent size of the new volume group, by default in
                bytes. 'T', 'G', 'M' or 'K' suffix can be used to use specify
                other units (TiB, GiB, MiB and KiB) - '1K' specifies 1 KiB
                (=1024 bytes).
                The suffix is case insensitive, i.e. 1g = 1G = 1073741824 bytes.
"""

from lmi.scripts.common import command
from lmi.scripts.storage import lvm, show
from lmi.scripts.storage.common import str2size, size2str, str2vg
from lmi.scripts.common.formatter import command as fcmd

class Lister(command.LmiLister):
    COLUMNS = ('InstanceID', 'ElementName', "ExtentSize", "Total space",
            "Free space")

    def execute(self, ns):
        """
        Implementation of 'vg list' command.
        """
        for vg in lvm.get_vgs(ns):
            extent_size = size2str(vg.ExtentSize,
                    self.app.config.human_friendly)
            total_space = size2str(vg.TotalManagedSpace,
                    self.app.config.human_friendly)
            remaining_space = size2str(vg.RemainingManagedSpace,
                    self.app.config.human_friendly)
            yield (vg.InstanceID,
                    vg.ElementName,
                    extent_size,
                    total_space,
                    remaining_space)


class Create(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Rename 'device' option to 'devices' parameter name for better
        readability.
        """
        options['<devices>'] = options.pop('<device>')

    def execute(self, ns, name, devices, _extent_size=None):
        """
        Implementation of 'vg create' command.
        """
        if _extent_size:
            _extent_size = str2size(_extent_size)
        lvm.create_vg(ns, devices, name, _extent_size)


class Delete(command.LmiCheckResult):
    EXPECT = None

    def transform_options(self, options):
        """
        Rename 'vg' option to 'vgs' parameter name for better
        readability.
        """
        options['<vgs>'] = options.pop('<vg>')

    def execute(self, ns, vgs):
        """
        Implementation of 'vg delete' command.
        """
        for vg in vgs:
            lvm.delete_vg(ns, vg)


class Show(command.LmiLister):
    COLUMNS = ('Name', 'Value')

    def transform_options(self, options):
        """
        Rename 'vg' option to 'vgs' parameter name for better
        readability.
        """
        options['<vgs>'] = options.pop('<vg>')

    def execute(self, ns, vgs=None):
        """
        Implementation of 'vg show' command.
        """
        if not vgs:
            vgs = lvm.get_vgs(ns)
        for vg in vgs:
            vg = str2vg(ns, vg)
            cmd = fcmd.NewTableCommand(title=vg.InstanceID)
            yield cmd
            for line in show.vg_show(ns, vg, self.app.config.human_friendly):
                yield line


Vg = command.register_subcommands(
        'vg', __doc__,
        { 'list'    : Lister ,
          'create'  : Create,
          'delete'  : Delete,
          'show'    : Show,
        },
    )
