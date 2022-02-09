/**
 * Author : Gérald FENOY
 *
 * Copyright (c) 2009-2013 GeoLabs SARL
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */
#ifndef __STRICT_AINSI__

#include <io.h>
#include <process.h>
#define mode_t int
#define strtok_r strtok_s
#define S_IRWXU _S_IREAD|_S_IWRITE
#define S_IRGRP _S_IREAD|_S_IWRITE
#define S_IROTH _S_IREAD|_S_IWRITE
#define S_IXGRP _S_IREAD|_S_IWRITE
#define S_IXOTH _S_IREAD|_S_IWRITE
#define S_IWOTH _S_IREAD|_S_IWRITE
#define S_IRUSR _S_IREAD
#define S_IXGRP _S_IREAD|_S_IWRITE
#define S_IWGRP _S_IREAD|_S_IWRITE
#define S_IWUSR _S_IREAD|_S_IWRITE

#endif
