import boto3
import base64


def kms_encrypt(plaintext, kms_key_id):
    kms_client = boto3.client("kms")

    cipher_text = kms_client.encrypt(
        KeyId=kms_key_id,
        Plaintext=bytes(plaintext, encoding="utf-8"),
    )
    cipher_text = base64.b64encode(cipher_text["CiphertextBlob"]).decode("utf-8")

    return cipher_text


print("input your plaintext: ", end="")
plaintext = input()
print("input your kms key id: ", end="")
kms_key_id = input()


print(f"cipher text:: \n{kms_encrypt(plaintext, kms_key_id)}")
