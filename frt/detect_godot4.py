# detect_godot4.py
#
# FRT - A Godot platform targeting single board computers
# Copyright (c) 2017-2023  Emanuele Fornara
# SPDX-License-Identifier: MIT
#

import os
import sys
import platform
import version

# TODO factor out common bits

def get_opts():
	from SCons.Variables import BoolVariable
	return [
		BoolVariable('use_llvm', 'Use llvm compiler', False),
		BoolVariable('use_lto', 'Use link time optimization', False),
		BoolVariable('use_static_cpp', 'Link libgcc and libstdc++ statically', False),
		('frt_std', 'C++ standard for frt itself (no/auto/c++98/...)', 'auto'),
		('frt_arch', 'Architecture (no/arm32v6/arm32v7/arm64v8/amd64)', 'no'),
		('frt_cross', 'Cross compilation (no/auto/<triple>)', 'no'),
		BoolVariable('frt_custom_renderer', 'Use custom renderer', False),
	]

def get_flags():
	return [
	]

def configure_compiler(env):
	if env['use_llvm']:
		env['CC'] = 'clang'
		env['CXX'] = 'clang++'
		env['LD'] = 'clang++'
		env.extra_suffix += '.llvm'

def configure_lto(env):
	if not env['use_lto']:
		return
	if env['use_llvm']:
		env.Append(CCFLAGS=['-flto=thin'])
		env.Append(LINKFLAGS=['-fuse-ld=lld', '-flto=thin'])
		env['AR'] = 'llvm-ar'
		env['RANLIB'] = 'llvm-ranlib'
	else:
		env.Append(CCFLAGS=['-flto'])
		env.Append(LINKFLAGS=['-flto'])
	env.extra_suffix += '.lto'

def configure_arch(env):
	if env['frt_arch'] == 'arm32v6':
		env.Append(CCFLAGS=['-march=armv6', '-mfpu=vfp', '-mfloat-abi=hard'])
		env.extra_suffix += '.arm32v6'
	elif env['frt_arch'] == 'arm32v7':
		env.Append(CCFLAGS=['-march=armv7-a', '-mfpu=neon-vfpv4', '-mfloat-abi=hard'])
		env.extra_suffix += '.arm32v7'
	elif env['frt_arch'] == 'arm64v8':
		env.Append(CCFLAGS=['-march=armv8-a'])
		env.extra_suffix += '.arm64v8'
	elif env['frt_arch'] != 'no':
		env.extra_suffix += '.' + env['frt_arch']

def configure_cross(env):
	if env['frt_cross'] == 'no':
		env['FRT_PKG_CONFIG'] = 'pkg-config'
		return
	if env['frt_cross'] == 'auto':
		triple = {
			'arm32v6': 'arm-linux-gnueabihf',
			'arm32v7': 'arm-linux-gnueabihf',
			'arm64v8': 'aarch64-linux-gnu',
			'amd64': 'x86_64-linux-gnu',
		}[env['frt_arch']]
	else:
		triple = env['frt_cross']
	if env['use_llvm']:
		env.Append(CCFLAGS=['-target', triple])
		env.Append(LINKFLAGS=['-target', triple])
	else:
		env['CC'] = triple + '-gcc'
		env['CXX'] = triple + '-g++'
	env['FRT_PKG_CONFIG'] = triple + '-pkg-config'
	# 交叉链接时 libSDL2.so 自身的依赖（libX11 / libgbm / libpulse / libdrm…）在 sysroot 里
	# 不全，ld 会把它们的符号算成"未定义"而链接失败。那些库由**目标机**在运行时提供
	# （掌机上是厂商改造版 SDL2，走 /usr/trimui/lib），故允许共享库带未解析符号。
	env.Append(LINKFLAGS=['-Wl,--allow-shlib-undefined'])

def configure_target(env):
	pass # use engine default

def configure_misc(env):
    env.Append(CPPPATH=['#platform/frt'])
    env.Append(CPPFLAGS=['-DUNIX_ENABLED'])
    env.Append(CPPDEFINES=[('_FILE_OFFSET_BITS', 64)])
    if env['vulkan']:
        env.Append(CPPDEFINES=['VULKAN_ENABLED'])
    if env['opengl3']:
        env.Append(CPPDEFINES=['GLES3_ENABLED'])
    env.Append(CPPFLAGS=['-DFRT_ENABLED'])
    env.Append(LIBS=['pthread', 'z', 'dl', 'EGL', 'GLESv2'])  # Added 'EGL' and 'GLESv2' here
    if env['CXX'] == 'clang++':
        env['CC'] = 'clang'
        env['LD'] = 'clang++'
    if env['use_static_cpp']:
        env.Append(LINKFLAGS=['-static-libgcc', '-static-libstdc++'])
    # Godot 4.7 默认 arch="auto"（产物名里的 .auto. 就是它），而 thirdparty/ 下几个库
    # 用 env["arch"] 精确匹配来决定要不要编 .S 汇编：
    #   arch=auto ⇒ 不编 .S；但 C 侧仍按编译器预定义宏启用 SIMD 路径 ⇒ 链接期未定义符号。
    # 已确认的两处（都是这条路子，不是各自独立的 bug）：
    #   - zstd  x86: HUF_decompress4X*_usingDTable_internal_fast_asm_loop
    #   - libpng arm: png_riffle_palette_neon / png_do_expand_palette_*_neon
    # 直接用官方关断宏（pngpriv.h:136 注释原文就写着 put -DPNG_ARM_NEON_OPT=0 in CPPFLAGS）。
    env.Append(CPPDEFINES=['ZSTD_DISABLE_ASM', 'PNG_ARM_NEON_OPT=0'])

def configure(env):
	configure_compiler(env)
	configure_lto(env)
	configure_arch(env)
	configure_cross(env)
	configure_target(env)
	configure_misc(env)
