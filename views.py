from django.shortcuts import render, get_object_or_404
from .models import Device, Log
import paramiko
import time
from datetime import datetime


def home(request):
    all_device = Device.objects.all()
    cisco_device = Device.objects.filter(vendor='cisco')
    huawei_device = Device.objects.filter(vendor='huawei')
    last_10_event = Log.objects.all().order_by('-id')[:10]
    context = {'all_device': len(all_device),
               'cisco_device': len(cisco_device),
               'huawei_device': len(huawei_device),
               'last_10_event': last_10_event
               }
    return render(request, 'home.html', context)


def devices(request):
    all_device = Device.objects.all()
    context = {'all_device': all_device}
    return render(request, 'devices.html', context)


def config(request):
    if request.method == 'GET':
        devices = Device.objects.all()
        cisco_device = Device.objects.filter(vendor='cisco')
        huawei_device = Device.objects.filter(vendor='huawei')
        context = {'devices': devices,
                   'mode': '设备配置',
                   'huawei_device': huawei_device,
                    'cisco_device': cisco_device
                   }
        return render(request, 'config.html', context)

    elif request.method == 'POST':
        result = []
        selected_device_id = request.POST.getlist('device')
        huawei_command = request.POST['huawei_command'].splitlines()
        cisco_command = request.POST['cisco_command'].splitlines()
        for x in selected_device_id:
            try:
                dev = get_object_or_404(Device, pk=x)
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(hostname=dev.ip_address, username=dev.username, password=dev.password,
                                   look_for_keys=False)
                #思科
                if dev.vendor.lower() == 'cisco':
                    conn = ssh_client.invoke_shell()
                    result.append(f'{dev.ip_address}上的运行结果:')
                    conn.send('conf t\n')
                    time.sleep(1)
                    for cmd in cisco_command:
                        conn.send(cmd + '\n')
                        time.sleep(3)
                        output = conn.recv(65535).decode('ascii')
                        result.append(output)
                #华为
                elif dev.vendor.lower() == 'huawei':
                    conn = ssh_client.invoke_shell()
                    result.append(f'{dev.ip_address}上的运行结果:')
                    conn.send('sys\n')
                    time.sleep(1)
                    for cmd in huawei_command:
                        conn.send(cmd + '\n')
                        time.sleep(1)
                        output = conn.recv(65535).decode('ascii')
                        result.append(output)

                log = Log(target=dev.ip_address, action='Configure', status='Success', time=datetime.now(),
                          messages='No Error')
                log.save()
            except Exception as error:
                log = Log(target=dev.ip_address, action='Configure', status='Error', time=datetime.now(), messages=error)
                log.save()
        result = '\n'.join(result)
        return render(request, 'verify_config.html', {'result': result})


def backup_config(request):
    if request.method == 'GET':
        devices = Device.objects.all()
        context = {'devices': devices}
        return render(request, 'backup_config.html', context)

    elif request.method == 'POST':
        result = []
        selected_device_id = request.POST.getlist('device')
        for x in selected_device_id:
            try:
                dev = get_object_or_404(Device, pk=x)
                ssh_client = paramiko.SSHClient()
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh_client.connect(hostname=dev.ip_address, username=dev.username, password=dev.password, look_for_keys=False)
                #思科
                if dev.vendor.lower() == 'cisco':
                    conn = ssh_client.invoke_shell()
                    conn.send('terminal length 0\n')
                    conn.send('show run\n')
                    time.sleep(2)
                    output = conn.recv(65535).decode('ascii')
                    now = datetime.now()
                    date = f'{now.month}_{now.day}_{now.year}'
                    f = open(f'C:\\configuration_backup\\{dev.ip_address}_{date}.txt', 'w+')
                    f.write(output)
                    result.append(f'{dev.ip_address}配置备份成功!')
                #华为
                elif dev.vendor.lower() == 'huawei':
                    conn = ssh_client.invoke_shell()
                    conn.send('dis cu\n')
                    time.sleep(2)
                    output = conn.recv(65535).decode('ascii')
                    now = datetime.now()
                    date = f'{now.month}_{now.day}_{now.year}'
                    f = open(f'C:\\Users\\1\\Desktop\\configuration_backup\\{dev.ip_address}.txt', 'w+')
                    f.write(output)
                    result.append(f'{dev.ip_address}配置备份成功!')
                log = Log(target=dev.ip_address, action='Backup Configuration', status='Success', time=datetime.now(), messages='No Error')
                log.save()

            except Exception as e:
                log = Log(target=dev.ip_address, action='Backup Configuration', status='Error', time=datetime.now(), messages=e)
                log.save()
                result.append(f'{dev.ip_address}配置备份失败，请查看日志!')

        result = '\n'.join(result)
        return render(request, 'verify_config.html', {'result': result})


def log(request):
    logs = Log.objects.all()
    context = {'logs': logs}
    return render(request, 'log.html', context)
