from reqable import *
import os
import struct
import zlib

SOURCE_IMAGE = os.path.expanduser('~/Desktop/tx.png')
TEMP_512 = os.path.expanduser('~/Desktop/.temp_512.png')
TEMP_256 = os.path.expanduser('~/Desktop/.temp_256.png')


def make_circle_avatar(img):
    from PIL import Image, ImageDraw
    size = img.size[0]
    mask = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size-1, size-1), fill=255)
    result = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    img_rgba = img.convert('RGBA')
    result.paste(img_rgba, (0, 0), mask)
    return result


def create_png_with_exact_size(source_path, target_size, output_path, image_size):
    try:
        from PIL import Image
        from io import BytesIO
    except ImportError:
        print('[Avatar] 需要安装 PIL: pip install Pillow')
        return False
    
    img = Image.open(source_path)
    target_w, target_h = image_size
    img_w, img_h = img.size
    ratio = max(target_w / img_w, target_h / img_h)
    new_w = int(img_w * ratio)
    new_h = int(img_h * ratio)
    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))
    img = make_circle_avatar(img)
    
    best_data = None
    best_diff = float('inf')
    
    def save_with_transparency(converted_img, buf, level, original_rgba):
        if converted_img.mode == 'P':
            buf_temp = BytesIO()
            converted_img.save(buf_temp, format='PNG', compress_level=level, optimize=True, transparency=0)
            buf.write(buf_temp.getvalue())
        else:
            converted_img.save(buf, format='PNG', compress_level=level, optimize=True)
    
    def convert_to_palette_with_transparency(img, colors):
        rgba = img.convert('RGBA')
        rgb = Image.new('RGB', rgba.size, (0, 0, 0))
        rgb.paste(rgba, mask=rgba.split()[3])
        p_img = rgb.quantize(colors=colors-1, method=Image.Quantize.MEDIANCUT)
        alpha = rgba.split()[3]
        palette = list(p_img.getpalette())
        new_palette = [0, 0, 0] + palette[:765]
        result = Image.new('P', rgba.size)
        result.putpalette(new_palette)
        pixels = list(p_img.getdata())
        alpha_data = list(alpha.getdata())
        new_pixels = []
        for i, (px, a) in enumerate(zip(pixels, alpha_data)):
            if a == 0:
                new_pixels.append(0)
            else:
                new_pixels.append(px + 1)
        result.putdata(new_pixels)
        return result
    
    modes = [
        ('RGBA', lambda i: i.convert('RGBA'), False),
        ('P255', lambda i: convert_to_palette_with_transparency(i, 255), True),
        ('P128', lambda i: convert_to_palette_with_transparency(i, 128), True),
        ('P64', lambda i: convert_to_palette_with_transparency(i, 64), True),
        ('P32', lambda i: convert_to_palette_with_transparency(i, 32), True),
        ('P16', lambda i: convert_to_palette_with_transparency(i, 16), True),
    ]
    
    for mode_name, converter, needs_transparency in modes:
        try:
            converted = converter(img)
            for level in range(0, 10):
                buf = BytesIO()
                if needs_transparency and converted.mode == 'P':
                    converted.save(buf, format='PNG', compress_level=level, optimize=True, transparency=0)
                else:
                    converted.save(buf, format='PNG', compress_level=level, optimize=True)
                data = buf.getvalue()
                diff = target_size - len(data)
                if 0 <= diff < best_diff:
                    best_data = data
                    best_diff = diff
                    print(f'[Avatar] {mode_name} lv{level}: {len(data)}b (差{diff})')
        except Exception as e:
            print(f'[Avatar] {mode_name} 错误: {e}')
            pass
    
    if best_data is None or best_diff < 0:
        print(f'[Avatar] 无法压缩到目标大小，请使用更简单的图片')
        return False
    
    padding = target_size - len(best_data)
    print(f'[Avatar] 最佳: {len(best_data)}b, 填充: {padding}b')
    
    if padding == 0:
        with open(output_path, 'wb') as f:
            f.write(best_data)
        return True
    
    if padding < 12:
        return False
    
    iend_pos = len(best_data) - 12
    if best_data[iend_pos+4:iend_pos+8] != b'IEND':
        iend_pos = best_data.rfind(b'IEND') - 4
        if iend_pos < 0:
            return False
    
    data_len = padding - 12
    text_len = max(0, data_len - 2)
    chunk_data = b'X\x00' + b'P' * text_len
    chunk_type = b'tEXt'
    crc = zlib.crc32(chunk_type + chunk_data) & 0xffffffff
    chunk = struct.pack('>I', len(chunk_data)) + chunk_type + chunk_data + struct.pack('>I', crc)
    final = best_data[:iend_pos] + chunk + best_data[iend_pos:]
    
    if len(final) != target_size:
        return False
    
    with open(output_path, 'wb') as f:
        f.write(final)
    return True


def onRequest(context, request):
    url = context.url
    if request.method != 'PUT':
        return request
    
    content_type = request.headers['Content-Type']
    if content_type is None or 'image' not in content_type:
        return request
    
    print(f'[Avatar] PUT {url[:80]}...')
    
    content_length = request.headers['Content-Length']
    if content_length is None:
        return request
    
    try:
        target_size = int(content_length)
    except:
        return request
    
    print(f'[Avatar] 目标: {target_size}b')
    
    if '_thn' in url:
        image_size = (256, 256)
        temp_file = TEMP_256
        print('[Avatar] 缩略图 256x256')
    else:
        image_size = (512, 512)
        temp_file = TEMP_512
        print('[Avatar] 原图 512x512')
    
    if not os.path.exists(SOURCE_IMAGE):
        print(f'[Avatar] 源图不存在: {SOURCE_IMAGE}')
        return request
    
    success = create_png_with_exact_size(SOURCE_IMAGE, target_size, temp_file, image_size)
    
    if success and os.path.getsize(temp_file) == target_size:
        print(f'[Avatar] ✓ 替换成功')
        request.body.binary(temp_file)
    else:
        print('[Avatar] ✗ 生成失败')
    
    return request


def onResponse(context, response):
    if 'cngf01-picture-upload' in context.url:
        if response.code == 200:
            print('[Avatar] ✓ 上传成功!')
        else:
            print(f'[Avatar] ✗ 失败: {response.code}')
    return response
