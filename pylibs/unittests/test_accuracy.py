#!/usr/bin/env python3
# Copyright (c) 2023, The OTNS Authors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the
#    names of its contributors may be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
import unittest
import tabulate

from OTNSTestCase import OTNSTestCase


class CslTests(OTNSTestCase):
    #override
    def setUp(self):
        super().setUp()
        self.ns.radiomodel = 'MutualInterference'

    def getStats(self, csl_off=False, acc=1, uncert=10):
        ns = self.ns

        # add Parent
        router = ns.add("router", 100, 100)
        ns.node_cmd(router, f"csl accuracy {acc}")
        ns.node_cmd(router, f"csl uncertainty {uncert}")
        ns.go(10)

        # add SED
        sed = ns.add("sed", 220, 100)

        if csl_off:
            ns.node_cmd(sed,"pollperiod 1000")
        else:
            ns.node_cmd(sed,"pollperiod 240000")
            ns.node_cmd(sed,"csl timeout 240")
            ns.node_cmd(sed,"csl period 1000000")

        ns.go(10)
        self.assertFormPartitions(1)

        # collect sleep data over 60 s
        ns.node_cmd(sed,"radio stats clear")
        ns.go(60)
        stats = ns.node_cmd(sed,"radio stats")

        ns.delete(sed)
        ns.delete(router)

        for stat in stats:
            if 'Rx Time:' in stat:
                rx = int(1000*float(stat.split(': ')[1].split('s')[0].strip()))
            if 'Sleep Time:' in stat:
                sleep = int(1000*float(stat.split(': ')[1].split('s')[0].strip()))

        return [acc, uncert, sleep, rx]

    def testAccuracy(self):
        results = []
        headers = ['Acc. (ppm)', 'Unc. (10 us)', 'Sleep (ms)', 'Rx (ms)', 'Rx incr. (ms)']

        values = [1, 10, 20, 50, 100, 255]

        ideal_stats = self.getStats(acc=0, uncert=0)
        ideal_active = ideal_stats[-1]
        ideal_stats.append(0)
        results.append(ideal_stats)

        for a in values:
            for u in values:
                csl_stats = self.getStats(acc=a, uncert=u)
                csl_active = csl_stats[-1]
                active_vs_ideal = csl_active - ideal_active
                csl_stats.append(active_vs_ideal)
                results.append(csl_stats)

        print(tabulate.tabulate(results, headers=headers, tablefmt='github'))


if __name__ == '__main__':
    unittest.main()
