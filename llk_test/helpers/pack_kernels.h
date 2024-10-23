#ifndef PACK_KERNELS_HPP
#define PACK_KERNELS_HPP

    #include <cstdint>
    #include <cstdarg>
    #define PROCESS_NUMBERS(n, ...) processNumbers(n, __VA_ARGS__)

    void pack_Dest_kernel();
    void nop();
    extern void(*kernels[10])(void);

    /* Function for assigning elemtens of kernerls array to some of kernels */
    inline void processNumbers(int n, int first, ...) {

        // Set the first kernel based on the first argument
        if(first == 1){
            kernels[0] = &pack_Dest_kernel;
        }else{
            kernels[0] = &nop;
        }

        va_list args;
        va_start(args, first);
        for (int i = 1; i < n; ++i) {
            int num = va_arg(args, int);
            if(num == 1){
                kernels[i] = &pack_Dest_kernel;
            } else {
                kernels[i] = &nop;
            }
        }
        va_end(args);
    }

#endif