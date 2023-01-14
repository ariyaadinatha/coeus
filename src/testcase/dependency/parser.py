import json

with open('package-lock.json', 'r') as file:
    dep = json.load(file)

true = True
a = {
    "requires": true,
    "lockfileVersion": 1,
    "dependencies": {
        "@babel/code-frame": {
            "version": "7.10.3",
            "resolved": "https://registry.npmjs.org/@babel/code-frame/-/code-frame-7.10.3.tgz",
            "integrity": "sha512-fDx9eNW0qz0WkUeqL6tXEXzVlPh6Y5aCDEZesl0xBGA8ndRukX91Uk44ZqnkECp01NAZUdCAl+aiQNGi0k88Eg==",
            "dev": true,
            "requires": {
                "@babel/highlight": "^7.10.3"
            }
        },
        "@babel/core": {
            "version": "7.10.3",
            "resolved": "https://registry.npmjs.org/@babel/core/-/core-7.10.3.tgz",
            "integrity": "sha512-5YqWxYE3pyhIi84L84YcwjeEgS+fa7ZjK6IBVGTjDVfm64njkR2lfDhVR5OudLk8x2GK59YoSyVv+L/03k1q9w==",
            "dev": true,
            "requires": {
                "@babel/code-frame": "^7.10.3",
                "@babel/generator": "^7.10.3",
                "@babel/helper-module-transforms": "^7.10.1",
                "@babel/helpers": "^7.10.1",
                "@babel/parser": "^7.10.3",
                "@babel/template": "^7.10.3",
                "@babel/traverse": "^7.10.3",
                "@babel/types": "^7.10.3",
                "convert-source-map": "^1.7.0",
                "debug": "^4.1.0",
                "gensync": "^1.0.0-beta.1",
                "json5": "^2.1.2",
                "lodash": "^4.17.13",
                "resolve": "^1.3.2",
                "semver": "^5.4.1",
                "source-map": "^0.5.0"
            },
            "dependencies": {
                "debug": {
                    "version": "4.1.1",
                    "resolved": "https://registry.npmjs.org/debug/-/debug-4.1.1.tgz",
                    "integrity": "sha512-pYAIzeRo8J6KPEaJ0VWOh5Pzkbw/RetuzehGM7QRRX5he4fPHx2rdKMB256ehJCkX+XRQm16eZLqLNS8RSZXZw==",
                    "dev": true,
                    "requires": {
                        "ms": "^2.1.1"
                    }
                },
                "ms": {
                    "version": "2.1.2",
                    "resolved": "https://registry.npmjs.org/ms/-/ms-2.1.2.tgz",
                    "integrity": "sha512-sGkPx+VjMtmA6MX27oA4FBFELFCZZ4S4XqeGOXCv68tT+jb3vk/RyaKWP0PTKyWtmLSM0b+adUTEvbs1PEaH2w==",
                    "dev": true
                }
            }
        },
        "@babel/generator": {
            "version": "7.10.3",
            "resolved": "https://registry.npmjs.org/@babel/generator/-/generator-7.10.3.tgz",
            "integrity": "sha512-drt8MUHbEqRzNR0xnF8nMehbY11b1SDkRw03PSNH/3Rb2Z35oxkddVSi3rcaak0YJQ86PCuE7Qx1jSFhbLNBMA==",
            "dev": true,
            "requires": {
                "@babel/types": "^7.10.3",
                "jsesc": "^2.5.1",
                "lodash": "^4.17.13",
                "source-map": "^0.5.0"
            }
        },
        "@babel/helper-module-imports": {
            "version": "7.10.3",
            "resolved": "https://registry.npmjs.org/@babel/helper-module-imports/-/helper-module-imports-7.10.3.tgz",
            "integrity": "sha512-Jtqw5M9pahLSUWA+76nhK9OG8nwYXzhQzVIGFoNaHnXF/r4l7kz4Fl0UAW7B6mqC5myoJiBP5/YQlXQTMfHI9w==",
            "dev": true,
            "requires": {
                "@babel/types": "^7.10.3"
            }
        },
        "@babel/helper-remap-async-to-generator": {
            "version": "7.10.3",
            "resolved": "https://registry.npmjs.org/@babel/helper-remap-async-to-generator/-/helper-remap-async-to-generator-7.10.3.tgz",
            "integrity": "sha512-sLB7666ARbJUGDO60ZormmhQOyqMX/shKBXZ7fy937s+3ID8gSrneMvKSSb+8xIM5V7Vn6uNVtOY1vIm26XLtA==",
            "dev": true,
            "requires": {
                "@babel/helper-annotate-as-pure": "^7.10.1",
                "@babel/helper-wrap-function": "^7.10.1",
                "@babel/template": "^7.10.3",
                "@babel/traverse": "^7.10.3",
                "@babel/types": "^7.10.3"
            }
        }
    }
}

# print(json.dumps(dep["dependencies"].values(), indent=4))
for name, content in (a["dependencies"].items()):
    print(name, content["version"])