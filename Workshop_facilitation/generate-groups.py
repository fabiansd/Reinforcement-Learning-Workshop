import logging
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
import os
import json
import argparse
import shutil
import pandas as pd

TMP_FOLDER = 'LINK_TEMP'
IP_DICT_JSON_NAME = 'active_ips.json'
GROUP_DICT_NAME = 'groups.json'


def bucket_exists(bucket_name):
    """Determine whether bucket_name exists and the user has permission to access it

    :param bucket_name: string
    :return: True if the referenced bucket_name exists, otherwise False
    """

    s3 = boto3.client('s3')
    try:
        response = s3.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        logging.debug(e)
        return False
    return True


def write_json(d, dest):
    with open(dest, 'w') as cred:
        json.dump(d, cred)


def load_json(dest):
    with open(dest, 'r') as cred:
        return json.load(cred)


def list_ec2():
    ec2 = boto3.client('ec2')
    response = ec2.describe_instances()

    running_ws_ips = {}

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:

            if instance['ImageId'] == 'ami-0573a1368e8959b03' \
                    and instance['State']['Name'] == 'running':

                running_ws_ips[instance['InstanceId']] = \
                    instance['NetworkInterfaces'][0]['Association']['PublicIp']

    print(f'\nFound the running ec2 instances:')
    print(f'{running_ws_ips}\n')

    return running_ws_ips


def download_files(bucket_name, LINK_FOLDER):

    ip_dict = list_ec2()

    if Path(TMP_FOLDER).exists():
        shutil.rmtree(TMP_FOLDER)
    os.mkdir(TMP_FOLDER)


    s3 = boto3.resource('s3')
    rl_bucket = s3.Bucket(bucket_name)

    # Downloads only files with an ip as name in the bucket
    for element in rl_bucket.objects.all():

        element_list = element.key.split('/')

        if element_list[0] == LINK_FOLDER and os.path.splitext(
                element_list[-1])[-1] == '.txt':
            p_ip, _ = os.path.splitext(element_list[-1])

            if p_ip in ip_dict.values():

                s3.meta.client.download_file(bucket_name,
                                             element.key,
                                             str(Path(TMP_FOLDER).joinpath(
                                                 element_list[-1])))

    # Save the ip dict to track last active ec2 instances
    write_json(ip_dict, IP_DICT_JSON_NAME)


def allocate_new_groups():

    ip_active_dict = load_json(IP_DICT_JSON_NAME)

    if Path(GROUP_DICT_NAME).exists():
        os.remove(Path(GROUP_DICT_NAME))

    group_dict = {}

    group_number = 1
    while True:

        popped_active_ip = ip_active_dict.pop(
            next(iter(ip_active_dict)))
        link_temp = ''
        try:
            with open(Path(TMP_FOLDER).joinpath(
                    popped_active_ip + '.txt'), 'r') as link_file:
                link_temp = link_file.read().replace('\n', '')
        except IOError:
            link_temp = 'NO LINK FOUND'

        group_dict[group_number] = {
            'ip': popped_active_ip,
            'link': link_temp
        }

        if len(ip_active_dict) == 0:
            break

        group_number += 1

    print('\nNew groups allocated to the running instances')
    print(group_dict)
    print('\n')

    write_json(group_dict, GROUP_DICT_NAME)


def update_and_allocate_instances(ip_active_dict):

    # ip_active_dict = load_json(IP_DICT_JSON_NAME)

    try:
        group_dict = load_json(Path(GROUP_DICT_NAME))
    except IOError:
        allocate_new_groups()
        return

    # If any groups no longer has a running EC2 among the active list,
    # remove the ip and link
    inactive_list = []
    for group_n, info_d in group_dict.items():
        if str(info_d['ip']) not in ip_active_dict.values():
            inactive_list.append(group_n)

    for n in inactive_list:
        group_dict[n] = {'ip': None, 'link': None}

    # This is untested

    # Here we round up the used ips og the active ips to find out what
    # active instances are vacant
    non_vacant_instances = []
    for group_n, info_d in group_dict.items():
        if not group_dict[group_n] == {'ip': None, 'link': None}:
            non_vacant_instances.append(group_dict[group_n]['ip'])


def test_connection(BUCKET_NAME):

    # Set up logging
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)s: %(asctime)s: %(message)s')

    # Check if the bucket exists
    if bucket_exists(BUCKET_NAME):
        logging.info(f'{BUCKET_NAME} exists and you have permission to access it.')
    else:
        logging.info(f'{BUCKET_NAME} does not exist or '
                     f'you do not have permission to access it.')


def generate_excel():

    group_dict = load_json(GROUP_DICT_NAME)

    group_df = pd.DataFrame.from_dict(group_dict, orient='index')

    group_df.to_excel('Groups.xlsx')

    print('Excel generated and saved')


if __name__ == '__main__':

    # Assign this value before running the program
    BUCKET_NAME = 'rl-workshop-bucket'
    LINK_FOLDER = 'RL-WS-links'

    # input arguments
    parser = argparse.ArgumentParser(description= 'Allocate running EC2 instances of RL-WS-image into groups')
    parser.add_argument('-i', '--init', required=True,
                        help='Set this to yes or no wheter you are creating the groups for the first time or updating')
    args = vars(parser.parse_args())

    test_connection(BUCKET_NAME)

    # Run script for fucntions
    # ip_org_dict = {'i-0345dc555876e6985': '54.174.112.245', 'i-0116da57317bfa93c': '3.87.192.207', 'i-0a2eb4c7cc444b410': '52.23.168.91'}
    # ip_new_dict = {'i-0345dc555876e6985': '54.174.112.245', 'i-0a2eb4c7cc444b410': '52.23.168.91'}
    # ip_replaced_dict = {'i-0116da57317bfa93c': '3.87.192.207', 'i-0116daas317bfa93c': '9.87.192.207', 'i-0a2eb4c7cc444b410': '52.23.168.91', 'i-0116da57317bfa93c': '3.87.192.207'}

    if args['init'] == 'yes':
        download_files(BUCKET_NAME, LINK_FOLDER)
        allocate_new_groups()
        generate_excel()

    elif args['init'] == 'no':
        download_files(BUCKET_NAME, LINK_FOLDER)
        update_and_allocate_instances()

    else:
        print('Invalid argument')







