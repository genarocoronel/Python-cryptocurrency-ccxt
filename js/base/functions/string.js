"use strict";

/*  ------------------------------------------------------------------------ */

module.exports =
    
    { uuid: a => a ? (a ^ Math.random () * 16 >> a / 4).toString (16)
                   : ([1e7]+-1e3+-4e3+-8e3+-1e11).replace (/[018]/g, uuid)
        
    , unCamelCase: s => s.replace (/[a-z][A-Z]/g, x => x[0] + '_' + x[1].toLowerCase ()) // fromCamelCase → from_camel_case

    , capitalize: s => s.length
                            ? (s.charAt (0).toUpperCase () + s.slice (1))
                            : s
    }

/*  ------------------------------------------------------------------------ */
