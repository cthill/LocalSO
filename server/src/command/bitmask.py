'''
Access to commands is granted using the admin_level (class) as a bitmask.
The admin_level is a byte with 2 bits unused, allowing for 6 groups of commands.

Admin 250 = 0b11111010

bit 0 = unused
bit 1 = group 1 commands
bit 2 = unused
bit 3 = group 2 commands
bit 4 = group 3 commands
bit 5 = group 4 commands
bit 6 = group 5 commands
bit 7 = admin commands

'''
BITMASK_ALL     = 0b00000000
BITMASK_NONE    = 0b00000101
BITMASK_GROUP_1 = 0b00000010
BITMASK_GROUP_2 = 0b00001000
BITMASK_GROUP_3 = 0b00010000
BITMASK_GROUP_4 = 0b00100000
BITMASK_GROUP_5 = 0b01000000
BITMASK_ADMIN   = 0b10000000
