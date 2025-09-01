echo "updating system"
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y git dfu-util
cd ..
echo "downloading custom klipper"
rm -rf klipper
git clone https://github.com/Melt3dDev/klipper
cd setup
echo "copying klipper config, mainsail theme and plymouth theme"
rm /home/biqu/printer_data/config/printer.cfg
cp printer.cfg /home/biqu/printer_data/config/
cp can.cfg /home/biqu/printer_data/config/
cp -r .theme /home/biqu/printer_data/config/
sudo rm /usr/share/plymouth/themes/armbian/bgrt-fallback.png
sudo cp bgrt-fallback.png /usr/share/plymouth/themes/armbian/
sudo rm /usr/share/plymouth/themes/armbian/watermark.png
sudo cp watermark.png /usr/share/plymouth/themes/armbian/
sudo rm /boot/armbiainEnv.txt
sudo cp armbiainEnv.txt /boot/
sudo rm /boot/system.cfg
sudo cp system.cfg /boot/
echo "Put Manta into boot mode"
read -p "Press enter to start flashing katapult to Manta"
sudo dfu-util -a 0 -D ~/setup/katapult_manta.bin --dfuse-address 0x08000000:force:leave -d 0483:df11
echo "Reset Manta, then put it into boot mode"
read -p "Press enter to start flashing klipper to Manta"
sudo dfu-util -a 0 -d 0483:df11 --dfuse-address 0x08020000 -D ~/setup/klipper_manta.bin
echo "Reset Manta again"
echo "Connect can via USB and put it into boot mode"
read -p "Press enter to start flashing katapult to Can"
sudo dfu-util -a 0 -D ~/setup/katapult_can.bin --dfuse-address 0x08000000:force:leave -d 0483:df11
echo "Reset Can, then put it into boot mode"
sudo dfu-util -a 0 -d 0483:df11 --dfuse-address 0x08002000 -D ~/klipper_can.bin
read -p "Disconnect Can USB then press enter"
sudo ifup can0
echo "Querying Manta UUID"
manta_uuid_querry=( $(python3 ~/setup/katapult/scripts/flash_can.py -q) )
manta_uuid=( $(echo ${manta_uuid_querry[11]::-1}) )
echo Manta UUID: $manta_uuid
read -p "Connect Can via cable then press enter"
echo "Querying Can UUID"
can_uuid_querry=( $(python3 ~/setup/katapult/scripts/flash_can.py -q) )
can_uuid=( $(echo ${manta_uuid_querry[16]::-1}) )
echo Manta UUID: $can_uuid
echo "Setting manta uuid"
echo [mcu] >> /home/biqu/printer_data/config/printer.cfg
echo canbus_uuid: $manta_uuid >> /home/biqu/printer_data/config/printer.cfg
echo canbus_interface: can0 >> /home/biqu/printer_data/config/printer.cfg
echo "Setting ebb can uuid"
echo [mcu EBBCan] >> /home/biqu/printer_data/config/can.cfg
echo canbus_uuid: $can_uuid >> /home/biqu/printer_data/config/can.cfg
echo canbus_interface: can0 >> /home/biqu/printer_data/config/can.cfg

