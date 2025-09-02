echo -e "\e[1m\e[32m ----Updating System---- \e[0m"
sudo apt-get update -y
sudo apt-get upgrade -y
cd
echo -e "\e[1m\e[32m ----Downloading modified Klipper---- \e[0m"
rm -rf klipper
git clone https://github.com/Melt3dDev/klipper
cd setup
echo -e "\e[1m\e[32m ----Copying Klipper config, Mainsail theme and Plymouth theme---- \e[0m"
rm /home/biqu/printer_data/config/printer.cfg
cp printer.cfg /home/biqu/printer_data/config/
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
echo -e "\e[1m\e[32m ----Flashing Manta---- \e[0m"
echo "Put Manta into boot mode"
read -p "Press enter to start flashing katapult to Manta"
sudo dfu-util -a 0 -D ~/setup/katapult_manta.bin --dfuse-address 0x08000000:force:leave -d 0483:df11
echo "Reset Manta, then put it into boot mode"
read -p "Press enter to start flashing klipper to Manta"
sudo dfu-util -a 0 -d 0483:df11 --dfuse-address 0x08020000 -D ~/setup/klipper_manta.bin
echo "Reset Manta again"
echo -e "\e[1m\e[32m ----Flashing EBB Can---- \e[0m"
echo "Reset Manta. Connect EBB Can via USB and put it into boot mode"
read -p "Press enter to start flashing katapult to EBB Can"
sudo dfu-util -a 0 -D ~/setup/katapult_can.bin --dfuse-address 0x08000000:force:leave -d 0483:df11
read -p "Reset EBB Can, then put it into boot mode"
sudo dfu-util -a 0 -d 0483:df11 --dfuse-address 0x08002000 -D ~/setup/klipper_can.bin
read -p "Disconnect EBB Can USB then press enter"
sudo ifup can0
echo -e "\e[1m\e[32m ----Querying Manta UUID---- \e[0m"
manta_uuid_querry=( $(python3 ~/setup/flash_can.py -q) )
manta_uuid=( $(echo ${manta_uuid_querry[11]::-1}) )
echo Manta UUID: $manta_uuid
read -p "Connect EBB Can via cable then press enter"
echo "Querying EBB Can UUID"
can_uuid_querry=( $(python3 ~/setup/flash_can.py -q) )
can_uuid=( $(echo ${manta_uuid_querry[16]::-1}) )
echo Manta UUID: $can_uuid
echo -e "\e[1m\e[32m ----Setting Manta uuid---- \e[0m"
echo [mcu] >> /home/biqu/printer_data/config/printer.cfg
echo canbus_uuid: $manta_uuid >> /home/biqu/printer_data/config/printer.cfg
echo canbus_interface: can0 >> /home/biqu/printer_data/config/printer.cfg
echo -e "\e[1m\e[32m ----Setting EBB Can uuid---- \e[0m"
echo [mcu EBBCan] >> /home/biqu/printer_data/config/can.cfg
echo canbus_uuid: $can_uuid >> /home/biqu/printer_data/config/can.cfg
echo canbus_interface: can0 >> /home/biqu/printer_data/config/can.cfg
echo -e "\e[1m\e[32m ----Restarting Klipper---- \e[0m"
sudo systemctl restart klipper
echo -e "\e[1m\e[32m ----Everything done---- \e[0m"

