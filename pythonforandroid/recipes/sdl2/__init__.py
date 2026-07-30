from os.path import exists, join

from pythonforandroid.recipe import BootstrapNDKRecipe
from pythonforandroid.toolchain import current_directory, shprint
import sh


class LibSDL2Recipe(BootstrapNDKRecipe):
    version = "2.30.11"
    url = "https://github.com/libsdl-org/SDL/releases/download/release-{version}/SDL2-{version}.tar.gz"
    md5sum = 'bea190b480f6df249db29eb3bacfe41e'

    conflicts = ['sdl3']

    dir_name = 'SDL'

    depends = ['sdl2_image', 'sdl2_mixer', 'sdl2_ttf']

    def get_recipe_env(self, arch=None, with_flags_in_cc=True, with_python=True):
        env = super().get_recipe_env(
            arch=arch, with_flags_in_cc=with_flags_in_cc, with_python=with_python)
        env['APP_ALLOW_MISSING_DEPS'] = 'true'
        return env

    def should_build(self, arch):
        libdir = join(self.get_build_dir(arch.arch), "../..", "libs", arch.arch)
        libs = ['libmain.so', 'libSDL2.so', 'libSDL2_image.so', 'libSDL2_mixer.so', 'libSDL2_ttf.so']
        return not all(exists(join(libdir, x)) for x in libs)

    def build_arch(self, arch):
        env = self.get_recipe_env(arch)

        jnidir = self.get_jni_dir()
        with current_directory(jnidir):
            # Disable bionic FORTIFY: NDK r25+ enables _FORTIFY_SOURCE=2 for release
            # builds, which makes SDL2's pthread_mutex_lock on a (sometimes already
            # destroyed) mutex abort with SIGABRT at startup. Force a debug optim
            # level (NDK adds no FORTIFY for debug) and also explicitly undefine
            # _FORTIFY_SOURCE as a belt-and-suspenders measure.
            amk = join(jnidir, "Application.mk")
            if exists(amk):
                c = open(amk).read()
                if "FORTIFY_SOURCE=0" not in c:
                    c += (
                        "\n"
                        "# Patched by baibao build: disable bionic FORTIFY (SDL2 destroyed-mutex SIGABRT)\n"
                        "APP_OPTIM := debug\n"
                        "APP_CFLAGS += -D_FORTIFY_SOURCE=0\n"
                        "APP_CPPFLAGS += -D_FORTIFY_SOURCE=0\n"
                    )
                    open(amk, "w").write(c)
            shprint(
                sh.Command(join(self.ctx.ndk_dir, "ndk-build")),
                "V=1",
                "NDK_DEBUG=" + ("1" if self.ctx.build_as_debuggable else "0"),
                _env=env
            )


recipe = LibSDL2Recipe()
