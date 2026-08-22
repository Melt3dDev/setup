# Setup instructions for Melta-MK1

## Boards using CB1 with SD Card
- SSH into the printer you want to set up.
```
ssh biqu@bigtreetech-cb1.local
```
```
password: biqu
```
- Clone branch:
```
git clone -b CB1-SD https://github.com/Melt3dDev/setup
```
- Prepare USB and CAN cable for EBB36.
- Go to setup directory and run setup script:
```
cd setup && ./setup.sh
```
- Follow the instructions.