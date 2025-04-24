import os
import struct
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib
import argparse

"""
9.建立一个不同于系统打包软件规则的自定义的文件群打包格式，
并编写符合这个打包格式的打包、解包软件。该软件启动时需要输
入一个秘钥，该秘钥以密文形式存储在软件中，也可以是把秘钥分
段存储在软件不相邻的数据空间，以增加破解难度。这个要求适应
于保护个人数据隐私，当电脑无意中被他人使用，或移动存储数据
被他人无意获取时，由于是个人格式打包存储，别人无法正常把数
据弹开，也就无法进行进一步的个人隐私数据破解。这种打包规则
越复杂，他人破解难度越大。
"""

# 自定义打包格式的魔数
MAGIC_NUMBER = b'CFGP'

# 版本号
VERSION = 1

# 秘钥相关
# SECRET_KEY = b'your_secret_key_here'  # 这里应该替换成你的秘钥，实际应用中需要更安全的存储方式
KEY_SALT = b'salt_for_key_derivation'


def derive_key(secret_key, salt):
    """派生加密密钥"""
    return hashlib.pbkdf2_hmac('sha256', secret_key, salt, 100000, dklen=32)


def pack_files(input_files, output_path,secret_key):
    """打包文件"""
    # 密钥派生
    derived_key = derive_key(secret_key, KEY_SALT)
    cipher = AES.new(derived_key, AES.MODE_CBC)

    # 文件头
    header = struct.pack('!4sI', MAGIC_NUMBER, VERSION)
    header += struct.pack('!16s16s', cipher.iv, derived_key[:16])  # 存储IV和部分派生密钥用于解包时验证

    # 文件数据区
    file_data = b''
    for file_path in input_files:
        with open(file_path, 'rb') as f:
            file_name = os.path.basename(file_path).encode('utf-8')
            file_size = os.path.getsize(file_path)
            file_content = f.read()

            # 加密文件内容
            encrypted_content = cipher.encrypt(pad(file_content, AES.block_size))

            # 构造文件条目
            file_entry = struct.pack('!I', len(file_name)) + file_name
            file_entry += struct.pack('!Q', file_size) + encrypted_content
            file_data += file_entry

    # 文件尾
    footer = struct.pack('!32s', hashlib.sha256(file_data).digest())  # 校验和

    # 写入打包文件
    with open(output_path, 'wb') as out_file:
        out_file.write(header)
        out_file.write(file_data)
        out_file.write(footer)

    print(f"文件打包完成，输出文件：{output_path}")


def unpack_file(input_path, output_dir,secret_key):
    """解包文件"""
    with open(input_path, 'rb') as in_file:
        # 读取文件头
        magic = in_file.read(4)
        if magic != MAGIC_NUMBER:
            raise ValueError("无效的文件格式")

        version = struct.unpack('!I', in_file.read(4))[0]
        iv = in_file.read(16)
        stored_key_part = in_file.read(16)

        # 密钥派生并验证
        derived_key = derive_key(secret_key, KEY_SALT)
        if stored_key_part != derived_key[:16]:
            raise ValueError("秘钥验证失败")

        cipher = AES.new(derived_key, AES.MODE_CBC, iv=iv)

        data_start = in_file.tell()

        # 读取文件数据区
        os.makedirs(output_dir, exist_ok=True)
        while True:
            # 读取文件名长度
            file_name_len_data = in_file.read(4)
            if not file_name_len_data:
                break
            file_name_len = struct.unpack('!I', file_name_len_data)[0]

            # 读取文件名
            file_name = in_file.read(file_name_len).decode('utf-8',errors="ignore")

            # 读取文件大小
            file_size_data = in_file.read(8)
            if len(file_size_data) != 8:
                print(f"读取文件大小数据不足，实际长度：{len(file_size_data)}")
                break
            file_size = struct.unpack('!Q', file_size_data)[0]

            # 读取加密后的文件内容
            encrypted_content = in_file.read((file_size + AES.block_size - 1) // AES.block_size * AES.block_size)
            decrypted_content = cipher.decrypt(encrypted_content)
            decrypted_content = unpad(decrypted_content, AES.block_size)

            # 保存解密后的文件
            output_path = os.path.join(output_dir, file_name)
            with open(output_path, 'wb') as out_f:
                out_f.write(decrypted_content)

        # 记录文件指针位置，用于计算校验和
        data_end = in_file.tell()

        # 读取文件尾校验和
        in_file.seek(-32, os.SEEK_END)
        actual_checksum = in_file.read(32)

        # 计算预期的校验和
        in_file.seek(data_start)
        data = in_file.read(data_end - data_start)
        expected_checksum = hashlib.sha256(data).digest()

        # 验证文件尾
        # expected_checksum = hashlib.sha256(in_file.read()[:-32]).digest()
        # actual_checksum = in_file.read(32)
        # if expected_checksum != actual_checksum:
        #     raise ValueError("文件校验失败，文件可能被篡改")

        print(f"文件解包完成，文件已保存到：{output_dir}")


"""
def main():
    parser = argparse.ArgumentParser(description='自定义文件打包/解包工具')
    parser.add_argument('-p', '--pack', nargs='+', help='打包文件列表')
    parser.add_argument('-u', '--unpack', help='解包文件路径')
    parser.add_argument('-o', '--output', help='输出文件或目录')

    args = parser.parse_args()

    if args.pack and args.output:
        pack_files(args.pack, args.output)
    elif args.unpack and args.output:
        unpack_file(args.unpack, args.output)
    else:
        print("用法：")
        print("打包：python script.py -p file1 file2 ... -o output.ccfg")
        print("解包：python script.py -u packed.ccfg -o output_dir")


if __name__ == "__main__":
    main()
"""