from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import os

#  5.软件支持文件的加密及解密，加密与解密算法自行选择，加密秘钥可输入（直接使用 python的库）

class FileEncryptor:
    def __init__(self):
        # AES 加密块大小为 128 位
        self.block_size = algorithms.AES.block_size

    def encrypt_file(self, input_file_path, output_file_path, key):
        """
        加密文件
        :param input_file_path: 输入文件路径
        :param output_file_path: 输出加密文件路径
        :param key: 加密秘钥（必须是 16、24 或 32 字节长）
        """
        # 检查秘钥长度是否有效
        if len(key) not in [16, 24, 32]:
            raise ValueError("秘钥长度必须是 16、24 或 32 字节")

        # 生成随机的初始向量（IV）
        iv = os.urandom(16)

        # 创建 AES CBC 模式的加密器
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # 读取文件内容并加密
        with open(input_file_path, 'rb') as f_in:
            # 读取文件内容
            file_data = f_in.read()

        # 对数据进行填充以满足块大小要求
        padder = padding.PKCS7(self.block_size).padder()
        padded_data = padder.update(file_data) + padder.finalize()

        # 加密数据
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

        # 将 IV 和加密数据写入输出文件
        with open(output_file_path, 'wb') as f_out:
            f_out.write(iv)
            f_out.write(encrypted_data)

        print(f"文件已加密并保存到 {output_file_path}")

    def decrypt_file(self, input_file_path, output_file_path, key):
        """
        解密文件
        :param input_file_path: 输入加密文件路径
        :param output_file_path: 输出解密文件路径
        :param key: 解密秘钥（必须与加密时使用的秘钥相同）
        """
        # 检查秘钥长度是否有效
        if len(key) not in [16, 24, 32]:
            raise ValueError("秘钥长度必须是 16、24 或 32 字节")

        # 读取加密文件内容
        with open(input_file_path, 'rb') as f_in:
            # 读取前 16 字节作为 IV
            iv = f_in.read(16)
            # 读取剩余内容作为加密数据
            encrypted_data = f_in.read()

        # 创建 AES CBC 模式的解密器
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        # 解密数据
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

        # 去除填充
        unpadder = padding.PKCS7(self.block_size).unpadder()
        unpadded_data = unpadder.update(decrypted_data) + unpadder.finalize()

        # 将解密后的内容写入输出文件
        with open(output_file_path, 'wb') as f_out:
            f_out.write(unpadded_data)

        print(f"文件已解密并保存到 {output_file_path}")

"""
使用说明
运行程序后，选择加密或解密操作。
输入要加密或解密的文件路径。
输入加密或解密后的输出文件路径。
输入秘钥（必须是 16、24 或 32 字节长）。
注意事项
秘钥必须是 16、24 或 32 字节长，这是 AES 算法的要求。
加密后的文件会包含一个 16 字节的初始向量（IV），用于解密时使用。
请妥善保管秘钥，否则将无法解密文件。
这个程序提供了一个基本的文件加密和解密功能，你可以根据需要扩展它，例如添加图形用户界面（GUI）或支持更多加密算法。
"""

"""
# 主程序
if __name__ == "__main__":
    encryptor = FileEncryptor()

    # 用户输入
    choice = input("选择操作：1. 加密文件  2. 解密文件\n")
    input_file = input("输入文件路径：\n")
    output_file = input("输出文件路径：\n")
    key = input("输入秘钥（必须是 16、24 或 32 字节）：\n").encode('utf-8')

    if choice == '1':
        encryptor.encrypt_file(input_file, output_file, key)
    elif choice == '2':
        encryptor.decrypt_file(input_file, output_file, key)
    else:
        print("无效的选择")
"""