
# General usage

If you want to graph values on the card you can do so by importing tt_arc_dbg_fw module and doing the following

```python
arc_fw = ArcDebugLoggerFw(ArcDfwLogContextFromYaml("default"))
arc_fw.load()

arc_fw.start_logging()

{{your code here}}

arc_fw.stop_loggging()
arc_fw.save_log_data_to_csv(log_data, csv_path)
arc_fw.save_graph_as_picture(log_data, f"{out_dir}/arc_fw.png")
```

# Log contexts

Log contexts are passed to ArcDebugLoggerFw so that it can know what to log

There are two types of LogContext
 - Yaml log context
 - List log context


## Yaml log context
Yaml log context can be loaded from any file, but there is a default one that can be used for everything.
Simply add what you want to log and the address of what you want to log to the file:

```yaml
logger_configuration:
  default:
    - power
    - current
    - curr_aiclk
    - ts_avg
    - voltage_at_fmax
    - voltage
  power:
    - power
  current:
    - current
```

Now you can just initialize yamllogcontext with the name of the configuration
```python
ArcDfwLogContextFromYaml("power")
```

## List log context
Using the addresses from a yaml file you can just say what you want to log without creating a logger configuration

```python
ArcDfwLogContextFromList(["power","current","scratch1"])
```
