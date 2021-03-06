#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
from cmd import Xar,Clang,Ld
from buildEnv import env

import xml.etree.ElementTree as ET
import  subprocess



class XarFile(object):

      def __init__(self,input):
        self.input = input
        self.dir = env.creatTmpDir()
        ExtraxmlCmd = ["-d", "-", "-f", input]
        retInfo = Xar(ExtraxmlCmd).run()
        self.xml = ET.fromstring(retInfo.stdout)
        Extracmd = ["-x", "-C", self.dir, "-f", input]
        Xar(Extracmd).run()


      @property
      def subdoc(self):
          return self.xml.find("subdoc")
      @property
      def toc(self):
          return self.xml.find("toc")

class Bitcode(XarFile):

      def __init__(self, arch, bundle, output):
          self.arch = arch
          self.bundle = bundle
          self.output = os.path.realpath(output)
          super(Bitcode, self).__init__(bundle)

          self.platform = "iPhoneOS"
          self.sdk_version = env.SDK_VER
          self.version = "1.0"
      def getAllFiles(self, type):
          return filter(lambda x: x.find("file-type").text == type, self.toc.findall("file"))

      def getobf(self):
          return ["-mllvm", "-bcf", "-mllvm", "-bcf_loop=3", "-mllvm", "-bcf_prob=40","-mllvm", "-fla","-mllvm", "-split", "-mllvm", "-split_num=2"]

      def consObj(self, xmlNode):
          name = os.path.join(self.dir, xmlNode.find("name").text)
          output = name + ".o"
          if xmlNode.find("clang") is not None:
            clang = Clang([name], [output])
            options = ['-triple', 'arm64-apple-ios8.0.0', '-emit-obj', '-target-abi', 'darwinpcs']
          clang.addArgs(options)
          clang.addArgs(self.getobf())
          return clang

      def doMore(self, works):
           return works.run()
      def doWork(self):
          l_inputs = []
          lin = Ld(self.output)
          lin.addArgs(["-arch", self.arch])
          lin.addArgs(["-ios_version_min", "8.0.0"])
          lin.addArgs(["-syslibroot", env.SDK])
          lin.addArgs(["-sdk_version", self.sdk_version])
          bitcodefiles = self.getAllFiles("Bitcode")

          bitcodeBundle = map(self.consObj, bitcodefiles)
          l_inputs.extend(bitcodeBundle)
          map(self.doMore, l_inputs)
          LinkFileList = os.path.join(self.dir, self.output + ".LinkFileList")
          with open(LinkFileList, 'w') as f:
             for i in [os.path.basename(x.output[0]) for x in l_inputs]:
                 f.write(os.path.join(self.dir, i))
                 f.write('\n')
          lin.addArgs(["-filelist", LinkFileList])
          lin.addArgs([env.SDK + "/System/Library/Frameworks/Foundation.framework/Foundation.tbd"])
          lin.addArgs([env.SDK + "/usr/lib/libobjc.A.tbd"])
          lin.addArgs([env.SDK + "/usr/lib/libSystem.B.tbd"])
          lin.addArgs([env.SDK + "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation.tbd"])
          lin.addArgs([env.SDK + "/System/Library/Frameworks/UIKit.framework/UIKit.tbd"])
          lin.addArgs([env.SDK + "/usr/lib/libobjc.A.tbd"])
          retinfo = self.doMore(lin)
          return self
