PROJECT=example

${PROJECT}.hex: main.c
	sdcc main.c -o $@


${PROJECT}.bin: ${PROJECT}.hex
	sdobjcopy -I ihex -O binary $<
