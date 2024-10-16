# Change the Google Services Framework ID (GSF ID)

# Requires the device to be rooted

# You can check the GSF ID with the Device Id for Android app (com.akademiteknoloji.androidallid)

adb shell settings delete secure android_id
adb shell settings delete secure advertising_id
adb shell settings delete secure bluetooth_address
adb shell su -c rm /data/system/users/0/accounts.db
adb shell su -c rm /data/system/users/0/accounts.db-journal
adb shell su -c rm /data/system/users/0/photo.png
adb shell su -c rm /data/system/users/0/settings_ssaid.xml
adb shell su -c rm /data/system/sync/accounts.xml
adb shell su -c rm /data/system/sync/pending.xml
adb shell su -c rm /data/system/sync/stats.bin
adb shell su -c rm /data/system/sync/status.bin
adb shell pm clear com.google.android.ext.services
adb shell pm clear com.google.android.ext.shared
adb shell pm clear com.google.android.gsf.login
adb shell pm clear com.google.android.onetimeinitializer
adb shell pm clear com.android.packageinstaller
adb shell pm clear com.android.providers.downloads
adb shell pm clear com.android.vending
adb shell pm clear com.google.android.backuptransport
adb shell pm clear com.google.android.gms
adb shell pm clear com.google.android.gms.setup
adb shell pm clear com.google.android.instantapps.supervisor
adb shell pm clear com.google.android.gsf

# Now set a new random device id with the Device ID Change app (com.silverlabtm.app.deviceidchanger.free)

# If you check the IDs in the Device Id for Android app, you should see that the Android Device ID and the Google Services Framework ID have changed.
