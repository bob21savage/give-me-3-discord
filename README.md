# give-me-3-discord
discord bot
automod details are https://github.com/bob21savage/give-me-3-discord
https://give-me-3-discord.onrender.com add discord automod
(?<url>^https:\/\/(?:(?:canary|ptb).)?discord(?:app)?.com\/api(?:\/v\d+)?\/webhooks\/(?<id>\d+)\/(?<token>[\w-]+)\/?$)
[^\f\n\r\t\v\u0020\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]
^.*([A-Za-z0-9]+( [A-Za-z0-9]+)+).*[A-Za-z]+.*$
^<@!?(?<id>\d{17,20})>$
^<@&(?<id>\d{17,20})>$
^<#(?<id>\d{17,20})>$
^https?:\/\/
^wss?:\/\/


extra regex patterns for discord automod below
(?<subdomain>\w+)\.?(?<hostname>dis(?:cord)?(?:app|merch|status)?)\.(?<tld>com|g(?:d|g|ift)|(?:de(?:sign|v))|media|new|store|net)

the process begins with this random regex you can add if you want

[a4]?+\s*[b8]+\s*c+\s*d+\s*[e3]?+\s*f+\s*[g9]+\s*h+\s*[i1l]?+\s*j+\s*k+\s*[l1i]+\s*(m|nn|rn)+\s*n+\s*[o0]?+\s*p+\s*q+\s*r+\s*[s5]+\s*[t7]+\s*[uv]?+\s*v+\s*(w|vv|uu)+\s*x+\s*y+\s*z+\s*0+\s*9+\s*8+\s*7+\s*6+\s*5+\s*4+\s*3+\s*2+\s*1+

