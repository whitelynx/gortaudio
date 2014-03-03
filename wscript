top = '.'
out = 'build'


import os
import re

from waflib import Logs, Task, TaskGen, Utils
from waflib.extras.swig import swigf
from waflib.extras.go import gopackage


def options(opt):
    opt.load('go swig gcc g++')
    opt.add_option('--exe', action='store_true', default=False, help='Execute the program after it is compiled')


def configure(ctx):
    ctx.load('go gcc g++ cgo')

    go_ver = Utils.subprocess.check_output(ctx.env['GO'] + ' version', shell=True)
    match = re.match(br'go version go(\d+)\.(\d+)(?:\.(\d+))? ', go_ver)
    if match.groups() < (b'1', b'1', None):
        ctx.fatal('this go version is too old')

    ctx.check_cfg(atleast_pkgconfig_version='0.0.0')

    ctx.load('swig')
    if ctx.check_swig_version() < (2, 0, 0):
        ctx.fatal('this swig version is too old')

    ctx.check_cfg(package='librtaudio')
    ctx.check_cfg(package='librtaudio', uselib_store='RTAUDIO', args=['--cflags', '--libs'])


def build(ctx):
    ctx(
            features='go gopackage cxx cxxshlib c',
            source='RtAudio.i',
            name='gortaudio',
            target='gortaudio',
            swig_flags='-c++ -go -intgosize 64 -Wall -package gortaudio',
            use=['RTAUDIO'],
            )


class go6g(Task.Task):
    run_str = '${GO_6G} ${GCFLAGS} -o ${TGT} ${SRC}'
    color = 'CYAN'
    before = ['gopackage']


class go6c(Task.Task):
    run_str = '${GO_6C} ${GCFLAGS} ${GO6C_INC_ST:GOINC} ${GO6C_INC_ST:INCPATHS} -o ${TGT} ${SRC}'
    color = 'CYAN'
    before = ['gopackage']


@TaskGen.feature('gopackage')
@TaskGen.before_method('modify_install_path')
def override_modify_install_path(self):
    """Override the default install path provided by the 'go' tool, correctly setting the package path."""
    if not self.env.GOSRC:
        self.env.GOSRC = os.path.join(self.env.GOPATH or self.env.GOROOT, 'src')

    if not self.env.GOMODULE:
        goModule = self.bld.srcnode.path_from(self.bld.root.find_dir(self.env['GOSRC']))
        self.env.GOMODULE = goModule
        self.env.GOMODULE_BASE = os.path.basename(goModule)
        self.env.GOMODULE_PREFIX = os.path.dirname(goModule)

    if not hasattr(self, 'install_path'):
        self.install_path = '${GOLIBDIR}/${GOMODULE_PREFIX}'


@swigf
def swig_go(self):
    if not self.generator.env['GO6C_INC_ST']:
        self.generator.env['GO6C_INC_ST'] = ['-I']

    if not self.generator.env['GOINC']:
        self.generator.env['GOINC'] = [self.generator.env['GOTOOLDIR'].replace('/tool/', '/')]

    self.generator.env.append_value('CFLAGS', self.generator.env.GOGCCFLAGS)
    self.generator.env.append_value('CXXFLAGS', self.generator.env.GOGCCFLAGS)
    self.generator.env.append_value('CFLAGS_cshlib', self.generator.env.GOGCCFLAGS)
    self.generator.env.append_value('CXXFLAGS_cxxshlib', self.generator.env.GOGCCFLAGS)

    goFile = self.inputs[0].parent.find_or_declare(self.module + '.go')
    gcFile = self.inputs[0].parent.find_or_declare(self.module + '_gc.c')
    shlibFile = self.inputs[0].parent.find_or_declare(self.module + '.so')

    goChar = self.env.GOCHAR

    goBuildTask = self.generator.create_task(
            'go6g',
            src=[goFile],
            tgt=[goFile.change_ext('.' + goChar)],
            )
    goBuildTask.set_run_after(self)

    gcBuildTask = self.generator.create_task(
            'go6c',
            src=[gcFile],
            tgt=[gcFile.change_ext('.' + goChar)],
            )
    gcBuildTask.set_run_after(self)

    shlibTask = self.generator.create_task(
            'cxxshlib',
            src=[],
            tgt=[shlibFile],
            )
    shlibTask.set_run_after(self)

    for t in self.generator.compiled_tasks:
        shlibTask.set_run_after(t)
        shlibTask.inputs.extend(t.outputs)

    shlibInstTask = self.generator.bld.install_files(
            getattr(self.generator, 'shlib_install_path', '${GOLIBDIR}/${GOMODULE_PREFIX}'),
            shlibTask.outputs[:], env=self.env, chmod=getattr(self, 'chmod', int('744', 8))
            )

    ge = self.generator.bld.producer
    ge.outstanding.insert(0, gcBuildTask)
    ge.outstanding.insert(0, goBuildTask)
    ge.outstanding.insert(0, shlibTask)
    ge.outstanding.append(shlibInstTask)
    ge.total += 3

    packTask = None
    for task in self.generator.tasks:
        if isinstance(task, gopackage):
            packTask = task

    if not packTask:
        Logs.warn('no gopackage task in %s' % self.generator)
    else:
        packTask.set_run_after(goBuildTask)
        packTask.set_run_after(gcBuildTask)
        packTask.inputs = [goBuildTask.outputs[0], gcBuildTask.outputs[0]]

    self.outputs.append(goFile)
    self.outputs.append(gcFile)
