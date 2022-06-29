# a200

![analyzer](https://i.ibb.co/hVkBDZd/Screenshot-from-2021-09-27-18-17-43.png)

### Commands

`Usage: ./a200 [command] [args]`

#### vw | view [layout(s)]
get a detailed view of a layout's metrics

examples:
- `./a200 view colemak`
- `./a200 view colemak semimak`

#### tc | toggle column [column]
change the visibility of column(s) or set(s) of columns. Use `all` to toggle all columns

examples:
- `./a200 tc roll`
- `./a200 tc LP RP`
- `./a200 tc all`

#### tl | toggle layout [layout]
change the visibility of layout(s)

examples:
- `./a200 tl dvorak`
- `./a200 tl qwerty dvorak colemak`

#### st | sort [parameter(s)]
order the results based on sort parameters. Parameters can be specified as either `(-)parameter` or `(-)x%parameter`, where a negative denotes sorting from low to high instead of high to low, and x denotes the percent weight of a given metric. If the weight of some parameters are unspecified, the weight will be divided equally among them

examples: 
- `./a200 sort roll`
- `./a200 sort -roll`
- `./a200 sort roll -redirect`
- `./a200 sort 70%roll -30%redirect`

#### fl | filter [parameter(s)]
filter the results based on a metrics and their cutoffs. Parameters are specified as `(-)x%metric`, where `x` is the cutoff, `metric` is the metric's name, and `-` includes only values *less* than the cutoff. Excluding `-` includes only values *greater* than the cutoff.

examples:
- `./a200 filter 50%roll`
- `./a200 filter 50%roll -1.5%sfb`

#### tb | thumb [LT, RT, NONE, AVG]
change which type of thumb to press space with. `LT` and `RT` represent the left and right thumb, respectively. `NONE` will throw away all trigram data with space. `AVG` will take the average of the metrics from left and right. 

examples:
- `./a200 thumb lt`
- `./a200 thumb rt`
- `./a200 thumb none`
- `./a200 thumb avg`

#### dt | data [data]
set the data to use in the analysis. [data] is the name of a file in the data/ directory.

examples:
- `./a200 data monkeytype-200`
- `./a200 data monkeytype-quotes`

#### tm | theme [theme]
set the color theme. [theme] is the name of a file in the themes/ directory.

examples:
- `./a200 theme autumn`
- `./a200 theme sunset`

#### cs | config save [filename]
saves the current config settings to a file in the configs/ directory

#### cl | config load [filename]
loads a config file from the configs/ directory

#### cc | cache clear []
clears the data cache

example:
- `./a200 cc`

#### reset []
set the config to its default factory state

example:
- `./a200 reset`

## Demo

a short [demo](https://youtu.be/eeS1HR6MgEE) of the command usage
