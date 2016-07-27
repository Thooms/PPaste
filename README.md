# PPaste

## How to run

```
$ mkdir pastes # directory that will store the paste files
$ python main.py --port=<port>
```
You can always `python main.py -h` to see some help.

## Highlight lines

In order to highlight lines, you need to provide `ln` in the query string.
You can highlight multiple lines by separating  your lines with `+`. You can specify a range of lines using `-`. For example, using `?ln=1+2+3-5` will
highlight lines 1, 2 and lines 3 to 5.

## Notes

* This project is licenced under MIT licence (see `LICENCE` file)
* It outputs logs on `STDIN`, please act accordingly if you want to monitor it
