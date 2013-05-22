top = '.'
out = 'build'


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
    #NOTE: if you use ant_glob, use it like this: bld.path.ant_glob('*.go', excl='*_test.go')

    #ctx(
    #        features='cxx go gopackage',
    #        source='RtAudio.i',
    #        target='gortaudio',
    #        swig_flags='-c++ -go -intgosize 64 -Wall -package gortaudio',
    #        use=['RTAUDIO'],
    #        )

    #ctx(
    #        #features='goswig cxx cxxshlib',
    #        features='cxx cxxshlib',
    #        source='RtAudio.i',
    #        target='RtAudioWrapper',
    #        swig_flags='-c++ -go -intgosize 64 -Wall -package gortaudio',
    #        use=['RTAUDIO'],
    #        )
    #ctx(
    #        features='cgo c go gopackage',
    #        name='gortaudio',
    #        target='gortaudio',
    #        use=['RtAudioWrapper'],
    #        )

    ctx(
            #features='goswig cxx cxxshlib',
            #features='go gopackage cxx cxxshlib cgo c',
            features='go gopackage cxx cxxshlib c',
            #features='go gopackage cxx cgo c',
            source='RtAudio.i',
            name='gortaudio',
            target='gortaudio',
            swig_flags='-c++ -go -intgosize 64 -Wall -package gortaudio',
            use=['RTAUDIO'],
            )

    #ctx.add_group()
    ctx(
            features='go goprogram uselib',
            source='test_gortaudio.go',
            target='test_gortaudio',
            use=['gortaudio'],
            #gocflags=['-I.', '-I..'],
            )


#@TaskGen.feature('goc')
#class goc(Task.Task):
#    color = 'CYAN'
#    run_str = '${GO_6C} ${GCFLAGS} ${GCPATH_ST:INCPATHS} -o ${TGT} ${SRC}'
#    ext_in = ['.c']
#    ext_out = ['.6']


class go6g(Task.Task):
    run_str = '${GO_6G} ${GCFLAGS} -o ${TGT} ${SRC}'
    color = 'CYAN'
    before = ['gopackage']


class go6c(Task.Task):
    run_str = '${GO_6C} ${GCFLAGS} ${GO6C_INC_ST:GOPKGDIR} ${GO6C_INC_ST:INCPATHS} -o ${TGT} ${SRC}'
    color = 'CYAN'
    before = ['gopackage']


@swigf
def swig_go(self):
    if not self.generator.env['GO6C_INC_ST']:
        self.generator.env['GO6C_INC_ST'] = ['-I']

    if not self.generator.env['GOPKGDIR']:
        self.generator.env['GOPKGDIR'] = [self.generator.env['GOTOOLDIR'].replace('/tool/', '/')]

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

    ge = self.generator.bld.producer
    ge.outstanding.insert(0, gcBuildTask)
    ge.outstanding.insert(0, goBuildTask)
    ge.outstanding.insert(0, shlibTask)
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

        #try:
        #    ltask = self.generator.link_task
        #except AttributeError:
        #    pass
        #else:
        #    packTask.inputs.append(ltask.outputs[0])

        #packTask.inputs.append(shlibTask.outputs[0])

    self.outputs.append(goFile)
    self.outputs.append(gcFile)


@TaskGen.feature('goswig')
@TaskGen.before('process_source', 'process_rule')
def dynamic_post(self):
    """
    bld(dynamic_source='*.c', ..) will search for source files to add to the attribute 'source'
    we could also call "eval" or whatever expression
    """
    if not getattr(self, 'dynamic_source', None):
        return
    self.source = Utils.to_list(self.source)
    self.source.extend(self.path.get_bld().ant_glob(self.dynamic_source, remove=False))
    #self.meths.append('infinite_loop')

    # if headers are created dynamically, assign signatures manually:
    # for x in self.path.get_bld().ant_glob('**/*.h', remove=False): x.sig = Utils.h_file(x.abspath())
