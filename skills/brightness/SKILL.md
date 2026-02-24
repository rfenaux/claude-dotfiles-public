# Brightness Control Skill

Control display brightness via BetterDisplay Pro settings.

## Trigger

`/brightness` or `/brightness <level>`

## Usage

```
/brightness          # Show current levels
/brightness max      # Maximum brightness (gain +30%)
/brightness high     # High brightness (gain +15%)
/brightness normal   # Normal brightness (gain 0%)
/brightness low      # Reduced brightness (gain -20%)
/brightness <0-150>  # Custom percentage (100 = normal)
```

## Examples

- `/brightness` - Check current brightness settings
- `/brightness max` - Crank it up for bright environments
- `/brightness 120` - Set to 120% (moderate boost)
- `/brightness normal` - Reset to default

## Implementation

<brightness>

### Parse Arguments

```
ARG=$1  # Level: max|high|normal|low|<number>
```

### Gain Mapping

| Level | Gain Value | Effect |
|-------|------------|--------|
| max | 0.30 | +30% brightness |
| high | 0.15 | +15% brightness |
| normal | 0.00 | Default |
| low | -0.20 | -20% brightness |
| Custom N | (N-100)/100 | N% of normal |

### Execution Steps

1. **If no argument**: Read and display current settings
   ```bash
   defaults read pro.betterdisplay.BetterDisplay | grep -E "value@(gain|hardwareBrightness|combinedBrightness).*@Display:2"
   ```

2. **If argument provided**: Set the gain value
   ```bash
   # Calculate gain based on level
   case "$ARG" in
     max)    GAIN=0.30 ;;
     high)   GAIN=0.15 ;;
     normal) GAIN=0.00 ;;
     low)    GAIN=-0.20 ;;
     *)      GAIN=$(echo "scale=2; ($ARG - 100) / 100" | bc) ;;
   esac

   # Apply settings
   defaults write pro.betterdisplay.BetterDisplay "value@gain-ColorController@Display:2" -float $GAIN
   defaults write pro.betterdisplay.BetterDisplay "value@hardwareBrightness-AppleController@Display:2" -float 1.0
   defaults write pro.betterdisplay.BetterDisplay forceXdrColorProfiles -bool true

   # Restart BetterDisplay
   killall BetterDisplay && sleep 1 && open -a BetterDisplay
   ```

3. **Confirm**: Display the new settings

### Output Format

```
Brightness: [LEVEL] (gain: [VALUE])
├─ Hardware: 100%
├─ Gain: +XX%
└─ XDR: enabled
```

</brightness>

## Notes

- Requires BetterDisplay Pro (you have it)
- Changes apply after BetterDisplay restart (~2 sec)
- Max brightness may reduce battery life
- Values persist across reboots
