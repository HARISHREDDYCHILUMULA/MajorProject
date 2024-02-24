array=[8,15,25,92,3,108,49,19,23,6] 
ma=array[0]
for i in range(1,len(array)):
	if ma<array[i]:
		ma=array[i]
return ma