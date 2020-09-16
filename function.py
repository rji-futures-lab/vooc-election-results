def main():
    print('Hello world!')


def lambda_handler(event, context):
    main()


if __name__ == '__main__':
    main()
