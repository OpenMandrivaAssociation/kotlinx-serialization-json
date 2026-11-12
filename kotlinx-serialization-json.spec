Name:		kotlinx-serialization-json
Version:	1.11.0
Release:	1
Summary:	Kotlin JSON serialization for the JVM
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/Kotlin/kotlinx.serialization
# kotlinx.serialization tag v1.11.0 (6956af2e6073347c7832c3c5b374fa3b5a345956).
# JVM classes for the catalog coordinate kotlinx-serialization-json.
# Upstream publishes that artifactId as a pom that points at the -jvm jar.
Source0:	kotlinx-serialization-json-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-21-openjdk-devel
BuildRequires:	kotlin
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-stdlib)
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-time-instant)
BuildRequires:	mvn(org.jetbrains.kotlinx:kotlinx-serialization-core)
BuildRequires:	mvn(org.jetbrains:annotations)

%description
org.jetbrains.kotlinx:kotlinx-serialization-json %{version}.
JVM JSON format from tag v1.11.0, compiled with kotlinc 2.0.21
against kotlinx-serialization-core 1.11.0.
FormatLanguage is a typealias to org.intellij.lang.annotations.Language.
IgnorableReturnValue annotations are omitted. They only affect the
return-value checker. Reserved discard bindings stay as bare calls.

%prep
%autosetup -n kotlinx-serialization-json-%{version}
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi
python3 - << 'PY'
from pathlib import Path
files = list(Path("src").rglob("*.kt"))
ign = 0
disc = 0
for p in files:
    text = p.read_text()
    ign += text.count("@IgnorableReturnValue\n")
    disc += text.count("val _ = ")
    text = text.replace("@IgnorableReturnValue\n", "")
    text = text.replace("val _ = ", "")
    p.write_text(text)
if len(files) != 45 or ign != 21 or disc != 7:
    raise SystemExit("patch counts files=" + str(len(files)) + " ign=" + str(ign) + " disc=" + str(disc))
for p in files:
    text = p.read_text()
    if "@IgnorableReturnValue" in text or "val _ = " in text:
        raise SystemExit("patch leftover " + str(p))
PY

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
STDLIB=%{_javadir}/kotlin-stdlib.jar
INSTANT=%{_javadir}/kotlin-time-instant.jar
CORE=%{_javadir}/kotlinx-serialization-core.jar
ANN=%{_javadir}/org.jetbrains.annotations.jar
test -s "$STDLIB"
test -s "$INSTANT"
test -s "$CORE"
test -s "$ANN"
mkdir -p classes
find src -name '*.kt' | sort > sources.list
find src/common -name '*.kt' | sort > common.list
test "$(wc -l < sources.list)" -eq 45
test "$(wc -l < common.list)" -eq 37
common=$(paste -sd, common.list)
kotlinc -J-Xmx2g -jvm-target 1.8 -language-version 2.0 -no-stdlib \
	-Xmulti-platform -Xexpect-actual-classes \
	-Xcommon-sources="$common" \
	-Xfriend-paths="$CORE" \
	-opt-in=kotlinx.serialization.InternalSerializationApi \
	-opt-in=kotlinx.serialization.ExperimentalSerializationApi \
	-opt-in=kotlinx.serialization.SealedSerializationApi \
	-opt-in=kotlin.ExperimentalSubclassOptIn \
	-opt-in=kotlin.time.ExperimentalTime \
	-opt-in=kotlin.ExperimentalMultiplatform \
	-opt-in=kotlinx.serialization.internal.CoreFriendModuleApi \
	-opt-in=kotlinx.serialization.json.internal.JsonFriendModuleApi \
	-cp "$STDLIB:$INSTANT:$CORE:$ANN" -d classes @sources.list
test "$(find classes -name '*.class' | wc -l)" -eq 130
test -s classes/kotlinx/serialization/json/Json.class
printf '%s\n' 'Manifest-Version: 1.0' 'Automatic-Module-Name: kotlinx.serialization.json' > manifest.mf
jar cfm kotlinx-serialization-json.jar manifest.mf -C classes .
jar i kotlinx-serialization-json.jar
desc=$(jar --describe-module --file kotlinx-serialization-json.jar)
printf '%s\n' "$desc"
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	exit 1
fi
printf '%s\n' "$desc" | grep -F -qx 'kotlinx.serialization.json automatic'
cat > kotlinx-serialization-json.pom << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.jetbrains.kotlinx</groupId>
  <artifactId>kotlinx-serialization-json</artifactId>
  <version>%{version}</version>
  <name>kotlinx-serialization-json</name>
  <description>Kotlin JSON serialization for the JVM</description>
  <url>https://github.com/Kotlin/kotlinx.serialization</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.jetbrains.kotlinx</groupId>
      <artifactId>kotlinx-serialization-core</artifactId>
      <version>%{version}</version>
    </dependency>
    <dependency>
      <groupId>org.jetbrains</groupId>
      <artifactId>annotations</artifactId>
      <version>26.1.0</version>
    </dependency>
  </dependencies>
</project>
END

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact kotlinx-serialization-json.pom:kotlinx-serialization-json.jar \
	--file-name kotlinx-serialization-json \
	--filelist .mfiles
idx="%{buildroot}/usr/share/sysjar/index/org.jetbrains.kotlinx/kotlinx-serialization-json.sysjar"
test -s "$idx"
grep -F -q '"version": "%{version}"' "$idx"
grep -F -q '"artifactId": "kotlinx-serialization-json"' "$idx"
test -s %{buildroot}%{_javadir}/kotlinx-serialization-json.jar

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
JAR=%{buildroot}%{_javadir}/kotlinx-serialization-json.jar
STDLIB=%{_javadir}/kotlin-stdlib.jar
INSTANT=%{_javadir}/kotlin-time-instant.jar
CORE=%{_javadir}/kotlinx-serialization-core.jar
ANN=%{_javadir}/org.jetbrains.annotations.jar
test -s "$JAR"
mkdir -p check
cat > check/Probe.kt << 'EOF'
import kotlin.time.Instant
import kotlinx.serialization.builtins.serializer
import kotlinx.serialization.json.Json

fun main() {
    val text = Json.encodeToString(String.serializer(), "gradle")
    val back = Json.decodeFromString(String.serializer(), text)
    val instant = Instant.fromEpochSeconds(42)
    val encoded = Json.encodeToString(Instant.serializer(), instant)
    val decoded = Json.decodeFromString(Instant.serializer(), encoded)
    if (back != "gradle" || decoded != instant) error("roundtrip")
    println("kotlinx_serialization_ok " + back.length + " " + decoded.epochSeconds)
}
EOF
kotlinc -J-Xmx1g -jvm-target 1.8 -language-version 2.0 \
	-opt-in=kotlin.time.ExperimentalTime \
	-cp "$JAR:$CORE:$INSTANT:$STDLIB:$ANN" -d check/out check/Probe.kt
java -cp "check/out:$JAR:$CORE:$INSTANT:$STDLIB:$ANN" ProbeKt > check/out.txt
cat check/out.txt
grep -F -qx 'kotlinx_serialization_ok 6 42' check/out.txt

%files -f .mfiles
%license LICENSE.txt
