import math
import argparse


def rotate_vector(x, y, z, angle_degrees):
    """
    绕Z轴旋转三维向量（适用于顶点、法向量等）
    :param x, y, z: 原始向量坐标
    :param angle_degrees: 旋转角度（度）
    :return: 旋转后的向量坐标
    """
    angle_radians = math.radians(angle_degrees)
    cos_theta = math.cos(angle_radians)
    sin_theta = math.sin(angle_radians)

    x_new = x * cos_theta - y * sin_theta
    y_new = x * sin_theta + y * cos_theta
    z_new = z  # Z坐标不变

    return x_new, y_new, z_new


def process_obj_file(input_file, output_file, angle):
    """处理OBJ文件，旋转所有顶点"""
    try:
        with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
            for line in f_in:
                line = line.strip()
                if not line:
                    f_out.write('\n')
                    continue

                parts = line.split()
                if parts[0] == 'v':  # 顶点数据
                    if len(parts) >= 4:
                        try:
                            x, y, z = map(float, parts[1:4])
                            x_new, y_new, z_new = rotate_vector(x, y, z, angle)

                            # 保留可能的w分量
                            if len(parts) == 5:
                                f_out.write(f"v {x_new:.6f} {y_new:.6f} {z_new:.6f} {parts[4]}\n")
                            else:
                                f_out.write(f"v {x_new:.6f} {y_new:.6f} {z_new:.6f}\n")
                        except ValueError:
                            f_out.write(line + '\n')
                    else:
                        f_out.write(line + '\n')
                else:
                    # 非顶点行（纹理坐标、面索引等）直接写入
                    f_out.write(line + '\n')

        print(f"成功处理OBJ文件: {input_file}")
        print(f"旋转角度: {angle}度")
        print(f"输出文件: {output_file}")

    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
    except Exception as e:
        print(f"处理OBJ文件时出错: {str(e)}")


def process_geo_file(input_file, output_file, angle):
    """处理GEO文件，旋转所有顶点和法向量"""
    try:
        with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
            for line in f_in:
                line = line.strip()
                if not line:
                    f_out.write('\n')
                    continue

                # 按逗号分割并去除空格
                parts = [p.strip() for p in line.split(',')]
                if not parts:
                    f_out.write(line + '\n')
                    continue

                # 处理法向量行 (fn)
                if parts[0] == 'fn':
                    if len(parts) >= 4:
                        try:
                            x, y, z = map(float, parts[1:4])
                            x_new, y_new, z_new = rotate_vector(x, y, z, angle)
                            # 保留可能的额外参数
                            extra = ','.join(parts[4:]) if len(parts) > 4 else ''
                            line_new = f"fn, {x_new:.6f}, {y_new:.6f}, {z_new:.6f}"
                            if extra:
                                line_new += f", {extra}"
                            f_out.write(line_new + '\n')
                        except ValueError:
                            f_out.write(line + '\n')
                    else:
                        f_out.write(line + '\n')

                # 处理面顶点行 (fv)
                elif parts[0] == 'fv':
                    if len(parts) >= 4:
                        try:
                            x, y, z = map(float, parts[1:4])
                            x_new, y_new, z_new = rotate_vector(x, y, z, angle)
                            extra = ','.join(parts[4:]) if len(parts) > 4 else ''
                            line_new = f"fv, {x_new:.6f}, {y_new:.6f}, {z_new:.6f}"
                            if extra:
                                line_new += f", {extra}"
                            f_out.write(line_new + '\n')
                        except ValueError:
                            f_out.write(line + '\n')
                    else:
                        f_out.write(line + '\n')

                # 处理孔径顶点行 (fh)
                elif parts[0] == 'fh':
                    if len(parts) >= 5:  # 格式: fh, aperture_num, x, y, z
                        try:
                            aperture_num = parts[1]
                            x, y, z = map(float, parts[2:5])
                            x_new, y_new, z_new = rotate_vector(x, y, z, angle)
                            extra = ','.join(parts[5:]) if len(parts) > 5 else ''
                            line_new = f"fh, {aperture_num}, {x_new:.6f}, {y_new:.6f}, {z_new:.6f}"
                            if extra:
                                line_new += f", {extra}"
                            f_out.write(line_new + '\n')
                        except ValueError:
                            f_out.write(line + '\n')
                    else:
                        f_out.write(line + '\n')

                # 其他行（面定义行f、分隔符;等）直接写入
                else:
                    f_out.write(line + '\n')

        print(f"成功处理GEO文件: {input_file}")
        print(f"旋转角度: {angle}度")
        print(f"输出文件: {output_file}")

    except FileNotFoundError:
        print(f"错误: 找不到文件 {input_file}")
    except Exception as e:
        print(f"处理GEO文件时出错: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description='将OBJ或GEO文件中的顶点/向量绕Z轴旋转指定角度')
    parser.add_argument('input', help='输入文件路径（支持.obj和.geo格式）')
    parser.add_argument('output', help='输出文件路径')
    parser.add_argument('angle', type=float, help='旋转角度（度，例如90表示旋转90度）')

    args = parser.parse_args()

    # 根据文件扩展名自动选择处理函数
    if args.input.endswith('.obj'):
        process_obj_file(args.input, args.output, args.angle)
    elif args.input.endswith('.geo'):
        process_geo_file(args.input, args.output, args.angle)
    else:
        print("错误: 仅支持.obj和.geo格式的文件")


if __name__ == "__main__":
    main()
