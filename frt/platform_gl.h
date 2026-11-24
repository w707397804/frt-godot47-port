// platform_gl.h
/*
  FRT - A Godot platform targeting single board computers
  SPDX-License-Identifier: MIT
 */

// Godot 4.3+ 把所有平台的 GL 入口统一成 "platform_gl.h"：
//   drivers/gles3/*.h 里写的是 #include <platform_gl.h>
// 4.1 及以前用的是另一套（platform_config.h 里的 OPENGL_INCLUDE_H），
// 所以 FRT 上游只有 platform_config.h、没有这个文件 —— 这是适配 4.7 新增的。
//
// FRT 不直接链 GLESv2，所有 GL 符号都靠 dl/gles3.dl 生成的函数指针表转发：
//   gen.h 里会生成 #define glBindBuffer frt_fn_gles3_glBindBuffer 之类的宏，
//   以及 extern FRT_FN_gles3_glBindBuffer frt_fn_gles3_glBindBuffer;
//   真正的地址由 frt_resolve_symbols_gles3() 在 EGL 上下文建好后填。
// 所以这里直接引生成出来的 gen.h（它本身已经 #include <GLES3/gl3.h>）。

#pragma once

#ifndef GLES_API_ENABLED
#define GLES_API_ENABLED
#endif

#include "dl/gles3.gen.h"
