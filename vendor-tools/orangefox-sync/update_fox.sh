#!/bin/bash
# ***************************************************************************************
# - Sync updates to OrangeFox; manifest-managed checkouts use repo sync only
# - Legacy minimal manifests also update separately cloned OrangeFox projects
# - Author:  DarthJabba9
# - Version: generic:009
# - Date:    22 September 2026
# ***************************************************************************************

# the version number of this script
SCRIPT_VERSION="20260922";

# Our starting point (Fox base dir)
BASE_DIR="$PWD";

# manifest directory
MANIFEST_DIR="";

# print a message and terminate with errorcode 1
abort() {
  echo "$@";
  exit 1;
}

# help
help_screen() {
  echo "Script to sync updates to the build system and OrangeFox sources";
  echo "Usage = $0 <arguments>";
  echo "Arguments:";
  echo "    -h, -H, --help 			print this help screen and quit";
  echo "    -d, -D, --debug 			debug mode: print each command being executed";
  echo "    -p, -P, --path <absolute_path>	root of the manifest checkout";
  echo "";
  echo "Examples:";
  echo "    $0 --path ~/OrangeFox_16.0";
  echo "    $0 --path ~/OrangeFox_14.1";
  echo "    $0 --path ~/OrangeFox_12.1";
  echo "    $0 --path ~/OrangeFox/fox_12.1 --debug";
  echo "";
  echo "- You must supply an *absolute* path for the '--path' switch";
  exit 0;
}

# process the command line arguments
Process_CMD_Line() {
    echo "$0, v$SCRIPT_VERSION";

   if [ -z "$1" ]; then
      help_screen;
   fi

   echo "- Script to sync updates to the build system and OrangeFox sources";

   while (( "$#" )); do
        case "$1" in
            # debug mode - show some verbose outputs
                -d | -D | --debug)
                        set -o xtrace;
                ;;
             # help
                -h | -H | --help)
                        help_screen;
                ;;
             # path
                -p | -P | --path)
                        shift;
                        [ -n "$1" ] && MANIFEST_DIR=$1;
                ;;
                *)
                        help_screen;
                ;;
        esac
     shift
   done

   [ -z "$MANIFEST_DIR" ] && help_screen;
   [ ! -d "$MANIFEST_DIR/bootable/" -o ! -d "$MANIFEST_DIR/build/" -o ! -d "$MANIFEST_DIR/external/"  ] && abort "- Invalid manifest directory: \"$MANIFEST_DIR\"";

   echo "- Starting the script ...";
   echo "- The working directory is: \"$BASE_DIR\"";
   echo "- The manifest root directory is: \"$MANIFEST_DIR\"";
}

# Execute the update
DoUpdate() {
local recovery=$MANIFEST_DIR/bootable/recovery;
local vendor=$MANIFEST_DIR/vendor/recovery;
local se_omapi=$MANIFEST_DIR/external/se_omapi;
local projects;

  cd "$MANIFEST_DIR" || abort "- Cannot enter manifest directory: \"$MANIFEST_DIR\"";
  projects=$(repo list --all --path-only) || abort "- Cannot read the effective manifest. Quitting.";
  # Complete manifests own both projects; legacy scripts clone the vendor separately.
  if grep -qx "bootable/recovery" <<< "$projects" && grep -qx "vendor/recovery" <<< "$projects"; then
     echo "- Updating all manifest-managed projects...";
     repo sync -c -j4 --no-clone-bundle --no-tags || abort "- Failed to sync the manifest-managed checkout. Quitting.";
     echo "- Finished.";
     cd "$BASE_DIR" || abort "- Cannot return to \"$BASE_DIR\"";
     exit 0;
  fi

  if [ ! -d "$recovery" ]; then
     abort "- Invalid recovery directory: \"$recovery\". Quitting.";
  elif [ ! -d "$vendor" ]; then
     abort "- Invalid vendor directory: \"$vendor\". Quitting.";
  fi
  
  # manifest
  echo "- Updating the build manifest...";
  echo "- You can ignore all errors relating to \"android_bootable_recovery\" or \"bootable/recovery\", etc ...";
  cd $MANIFEST_DIR && repo sync;
  
  # recovery sources
  cd $recovery && git pull;
  
  # vendor tree
  echo "- Updating the OrangeFox vendor tree ...";
  cd $vendor && git pull;

  # se_omapi
  if [ -d $se_omapi ]; then
	cd $se_omapi && git pull;
  fi

  # finish
  echo "- Finished.";
  cd $BASE_DIR;
  exit 0;
}

# main()
Process_CMD_Line "$@";
DoUpdate;
#
