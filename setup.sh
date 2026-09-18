echo -e "\e[1m\e[32m ----Updating System---- \e[0m"
sudo apt-get update -y
sudo apt-get upgrade -y
cd
echo -e "\e[1m\e[32m ----Downloading modified Klipper---- \e[0m"
rm -rf /home/biqu/klipper
git clone -b dev https://github.com/Melt3dDev/klipper
rm -rf /home/biqu/KlipperScreen
git clone https://github.com/Melt3dDev/KlipperScreen
cd setup
echo -e "\e[1m\e[32m ----Flashing Manta---- \e[0m"
echo -e "\e[1m\e[33m Put Manta into boot mode (Hold BOOT0 and short press RESET, after that release BOOT0) \e[0m"
read -p "Press enter to start flashing katapult to Manta"
sudo dfu-util -a 0 -D ~/setup/katapult_manta.bin --dfuse-address 0x08000000:force:leave -d 0483:df11
echo -e "\e[1m\e[33m Reset Manta (short press RESET), then put it into boot mode (Hold BOOT0 and short press RESET, after that release BOOT0) \e[0m"
read -p "Press enter to start flashing klipper to Manta"
sudo dfu-util -a 0 -d 0483:df11 --dfuse-address 0x08020000 -D ~/setup/klipper_manta.bin
echo -e "\e[1m\e[32m ----Flashing EBB Can---- \e[0m"
echo -e "\e[1m\e[33m Reset Manta (short press RESET). Connect EBB Can via USB and CAN cable and put it into boot mode (Hold BOOT and short press RST, after that release BOOT) \e[0m"
read -p "Press enter to start flashing katapult to EBB Can"
sudo dfu-util -a 0 -D ~/setup/katapult_can.bin --dfuse-address 0x08000000:force:leave -d 0483:df11
echo -e "\e[1m\e[33m Reset EBB Can (short press RST) and put it into boot mode (Hold BOOT and short press RST, after that release BOOT) \e[0m"
read -p "Press enter to start flashing klipper to EBB Can"
sudo dfu-util -a 0 -d 0483:df11 --dfuse-address 0x08002000 -D ~/setup/klipper_can.bin
echo -e "\e[1m\e[33m Disconnect EBB Can USB and CAN cable \e[0m"
read -p "Press enter when ready"
sudo ifup can0
echo -e "\e[1m\e[32m ----Querying Manta UUID---- \e[0m"
manta_uuid_querry=( $(python3 ~/setup/flash_can.py -q) )
manta_uuid=( $(echo ${manta_uuid_querry[11]::-1}) )
echo Manta UUID: $manta_uuid
echo -e "\e[1m\e[33m Connect EBB Can via CAN cable \e[0m"
read -p "Press enter when ready"
echo "Querying EBB Can UUID"
can_uuid_querry=( $(python3 ~/setup/flash_can.py -q) )
can_uuid=( $(echo ${can_uuid_querry[16]::-1}) )
echo Can UUID: $can_uuid
echo -e "\e[1m\e[32m ----Setting Manta uuid---- \e[0m"
head -n 9 ./printer.cfg > temp.cfg
echo [mcu] >> temp.cfg
echo canbus_uuid: $manta_uuid >> temp.cfg
echo canbus_interface: can0 >> temp.cfg
tail -n +11 ./printer.cfg >> temp.cfg
mv temp.cfg printer.cfg
echo -e "\e[1m\e[32m ----Setting EBB Can uuid---- \e[0m"
echo " " >> can.cfg
echo "[mcu EBBCan]" >> can.cfg
echo canbus_uuid: $can_uuid >> can.cfg
echo canbus_interface: can0 >> can.cfg
echo -e "\e[1m\e[32m ----Copying Klipper config, Mainsail theme and Plymouth theme---- \e[0m"
rm /home/biqu/printer_data/config/printer.cfg
rm /home/biqu/printer_data/config/KlipperScreen.conf
rm /home/biqu/printer_data/config/crowsnest.conf
cp KlipperScreen.conf /home/biqu/printer_data/config/
cp printer.cfg /home/biqu/printer_data/config/
cp Orbiter2_SmartSensor.cfg /home/biqu/printer_data/config/
cp crowsnest.conf /home/biqu/printer_data/config/
cp can.cfg /home/biqu/printer_data/config/
cp -r .theme /home/biqu/printer_data/config/
sudo rm /usr/share/plymouth/themes/armbian/bgrt-fallback.png
sudo cp bgrt-fallback.png /usr/share/plymouth/themes/armbian/
sudo rm /usr/share/plymouth/themes/armbian/watermark.png
sudo cp watermark.png /usr/share/plymouth/themes/armbian/
sudo rm /boot/armbianEnv.txt
sudo cp armbianEnv.txt /boot/
sudo rm /boot/system.cfg
sudo cp system.cfg /boot/
sudo systemctl disable NetworkManager-wait-online.service
sudo tee /usr/local/bin/tzupdate >/dev/null <<'EOF'
#!/bin/sh
TZ=$(curl -sf --max-time 10 https://ipapi.co/timezone)
[ -z "$TZ" ] && TZ=$(curl -sf --max-time 10 http://ip-api.com/line/?fields=timezone)
[ -z "$TZ" ] && exit 1
[ -f "/usr/share/zoneinfo/$TZ" ] || exit 1
[ "$TZ" = "$(timedatectl show -p Timezone --value)" ] && exit 0
timedatectl set-timezone "$TZ"
EOF
sudo chmod +x /usr/local/bin/tzupdate
sudo tzupdate
echo -e "\e[1m\e[32m ----Installing Obico---- \e[0m"
cd ~
git clone https://github.com/TheSpaghettiDetective/moonraker-obico.git
cd moonraker-obico
./install.sh -L -H 127.0.0.1 -p 7125 -C /home/biqu/printer_data/config/moonraker.conf -l /home/biqu/printer_data/logs -S https://meltvm.chocolate-cliff.ts.net
echo "biqu ALL=(root) NOPASSWD: /usr/bin/systemctl stop moonraker-obico, /usr/bin/systemctl restart moonraker-obico" | sudo tee /etc/sudoers.d/klipperscreen-obico
sudo chmod 0440 /etc/sudoers.d/klipperscreen-obico
echo -e "\e[1m\e[32m ----Restarting Klipper---- \e[0m"
sudo systemctl restart klipper
sudo systemctl restart KlipperScreen
echo -e "\e[1m\e[32m ----Everything done---- \e[0m"
echo -e "\e[1m\e[32m ----Rebooting---- \e[0m"
sudo reboot
