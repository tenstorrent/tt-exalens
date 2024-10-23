#ifndef MATH_KERNELS_HPP
#define MATH_KERNELS_HPP

    #include <cstdint>
    #include <cstdarg>
    #define PROCESS_NUMBERS(n, ...) processNumbers(n, __VA_ARGS__)
    
    void elwadd_kernel();
    void elwsub_kernel();
    void elwmul_kernel();
    void nop();
    
    extern void(*kernels[10])(void);

    /* Function for assigning elemtens of kernerls array to some of kernels */
    inline void processNumbers(int n, int first, ...) {

        // Set the first kernel based on the first argument
        if(first == 1){
            kernels[0] = &elwadd_kernel;
        } else if(first == 2){
            kernels[0] = &elwsub_kernel;
        }else if(first == 3){
            //kernels[0] &elwmul_kernel
        }
        else {
            kernels[0] = &nop;
        }

        va_list args;
        va_start(args, first);
        for (int i = 1; i < n; ++i) {
            int num = va_arg(args, int);
            if(num == 1){
                kernels[i] = &elwadd_kernel;
            } else if(num == 2){
                kernels[i] = &elwsub_kernel;
            }else if(num == 3){
                //kernels[i] &elwmul_kernel
            }
            else {
                kernels[i] = &nop;
            }
        }
        va_end(args);
    }

#endif