/*******************************************************************************
* int WWW_GetParam(name, index, value, maxchars)
*
* This internal function looks up a symbol and returns its value as a character
* string.  It returns a null string if the symbol is undefined.  This is the C
* function called by FORTRAN routine WWW_Lookup().
*
* Input:
*       name            symbol name.
*       index           starting index to search in list.
*       maxchars        maximum length of returned string
*
* Output:
*       value           symbol value, or an empty string if the symbol is not
*                       found.
*
* Return:               index of next search for repeated searches.
*******************************************************************************/
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

char    **strings = NULL;
char    **getcgivars();

int     www_getparam_(char *name, int *index, char *value, int *maxchars)
{
int     i, test;

        if (strings == NULL) strings = getcgivars();

        for (i = *index; strings[i] != NULL; i += 2) {
            test = strcmp(strings[i], name);

            if (test == 0) {
                strncpy(value, strings[i+1], *maxchars);
                return i+2;
            }
        }

        value[0] = '\0';
        return 0;
}

/******************************************************************************/
